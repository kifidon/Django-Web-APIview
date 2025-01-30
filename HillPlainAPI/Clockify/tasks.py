from celery import shared_task
from .serializers import *
from .models import *
from django.core.handlers.asgi import ASGIRequest
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import  utils 
from rest_framework.exceptions import ValidationError
from rest_framework import status
from asgiref.sync import sync_to_async
from BackgroundTasks.tasks import taskResult
from json import dumps
from HillPlainAPI.Loggers import setup_background_logger
from Utilities.clockify_util.ClockifyPullV3 import getCategories, getApiKey, getDataForApproval
from Utilities.views import hash50, bytes_to_dict, check_category_for_deletion, reverseForOutput, pauseOnDeadlock
from LemApplication.models import *
from LemApplication.serializers import *
import requests
import asyncio

loggerLevel = 'INFO'
logger = setup_background_logger(loggerLevel) #pass level argument 


def putTags(inputdata: dict):
    '''
    Function Description: 
        Inserts/Updates tags for a given time entry. Checks to delete any stale tags first  

        Transactions are not atomic 

    Param: 
        inputData(dict): Input data used in the entry function. required data is taken from this dict  
    
    Returns: 
        tags_data([dict]): List of all the tags_data that was used to update/insert into the  databse 

    Raises: 
        ValidationError 
        General Exception  
    '''
    try:
        logger.info(f'UpdateTags Function called')
        logger.debug(dumps(inputdata, indent =4))
        workspaceId = inputdata['workspaceId']
        tags_data = inputdata.get('tags')
        entry_id = inputdata.get("id")
        for i in range(0, len(tags_data)):
            logger.debug(dumps(tags_data, indent =4))
            tag = tags_data[i]
            logger.info(f'Update TagsFor on Entry {entry_id}: Complete ')
             
            # Create new tags
            logger.debug(f"Tags Data - {dumps(tags_data, indent= 4)}")
            tag['recordId'] = hash50(50, entry_id, tag['id'], workspaceId)
            try: 
                tag['entryid'] = entry_id
                tagObj = Tagsfor.objects.get(id=tag["id"], entryid = entry_id, workspaceId = workspaceId)
                serializer = TagsForSerializer(data=tag, instance=tagObj, partial=True)
                logger.warning('Updating Tag')
            except Tagsfor.DoesNotExist:
                serializer = TagsForSerializer(data=tag )
                logger.info(f'Creating new tag')
            if serializer.is_valid():
                logger.debug("Saving Tag Data for entry")
                serializer.save()
                logger.info("Opperation Succsesful")
                logger.info(f'UpdateTags on Entry: E-{entry_id}-T-{tag["id"]} ACCEPTED') 
            else: 
                logger.debug(f'Could not validate data\n{dumps(serializer.errors, indent=4)}')
                raise ValidationError(serializer.errors)

        return tags_data
    except Exception as e: 
        logger.info(f'Unhandled Exception ({e.__traceback__.tb_lineno}): {str(e)} in {e.__traceback__.tb_frame} ')
        raise e

def processPut(entries, workspaceId, timeId, inputData): # create thread
    logger.info('\t\tStarting Entry Store Process') 
    try: 
        #refactoring 
        entries['workspaceId']= workspaceId
        entries['timesheetId'] = entries['approvalRequestId'] or timeId
        try: # try and update if exists, otherwise create
            entry = Entry.objects.get(id = entries["id"], workspaceId = workspaceId )
            serializer = EntrySerializer(data=entries, instance=entry, context = {'workspaceId': workspaceId,'timesheetId': timeId})
            logger.info(f'Updating Entry {entries["id"]}')
        except Entry.DoesNotExist:
            serializer = EntrySerializer(data=entries, context = {'workspaceId': workspaceId,'approvalRequestId': timeId})
            logger.warning(f'Creating new Entry on timesheet {timeId}')

        if serializer.is_valid():
            serializer.save()
            logger.info(f'UpdateEntries on timesheet({timeId}): E-{entries["id"]} ACCEPTED') 
            reversed_data = reverseForOutput(entries)
            logger.debug(f'{reversed_data}') 
            if (len(entries['tags']) != 0):
                putTags(entries)
            return serializer.validated_data
        else: 
            logger.debug(f'{serializer.errors}') # For debugging 
            raise ValidationError(serializer.errors)
    except Exception as e:
        logger.error(f'{str(e)} at line {e.__traceback__.tb_lineno} in \n\t{e.__traceback__.tb_frame}') 
        raise e
                    
sem = asyncio.Semaphore(1)

async def putBatchEntries(inputData: dict): 
    '''
    Function Description: 
        Prepares timesheets for a timesheet on approved timesheets. Called from updateTimesheet function as a async background task. 
        Pulls data directly from clockify for the respected timesheet 
        Result of the task function is stored in the database table 'BackGroundTaskDjango'. Transactions are not atomic 

    Param: 
        inputData(dict): contains the the body of the request sent to the main server in the updateTimesheet function    
    Returns: 
        response(JsonResponse): Return value 
    '''
    #entry Function  
    logger.info("Running Batch Entry Function")
    try:
        logger.debug(dumps(inputData,indent=4))
        key = getApiKey()
        timeId = inputData.get("id")
        workspaceId = inputData.get('workspaceId')
        state = inputData.get('status').get('state') or None
    
        if state  not in ('APPROVED', 'PENDING'): # Entries cannot change on withdrawn/rejected timesheet events 
            logger.info(f'UpdateEntries on timesheet({timeId}): Update on Withdrawn timesheet not necessary: {state}')
            response = JsonResponse(data = {"Message": None}, status=status.HTTP_204_NO_CONTENT)
        else:
            allEntries = await getDataForApproval(workspaceId, key, timeId, state, entryFlag=True)
            if len(allEntries) == 0: #timesheet has no entries 
                logger.warning('No Content. Is this expected?') #some timesheet may be expenses only. This could also be an error where timesheet is not found 
                response =  JsonResponse(data = {f'Message': f'No Entry for timesheet {timeId}'}, status=status.HTTP_204_NO_CONTENT)
            
            for i in range(0,len(allEntries)): # updates all entries sync 
                logger.debug('\tWaiting for Approved Entry Semaphore')
                async with sem:
                    logger.debug('\tAquired Approved Entry Semaphore')
                    await sync_to_async(processPut, thread_sensitive=True)(allEntries[i], workspaceId, timeId, inputData)
                logger.debug('\tReleasing Approved Entry Semaphore')
            
            response = JsonResponse(data = {"Message":'Approved Entries Opperation Completed Succesfully'}, status=status.HTTP_201_CREATED)
            logger.info(f'All Entries added for timesheet {timeId}') 

    except Exception as e:
            logger.critical(f'{str(e)} at line {e.__traceback__.tb_lineno} in \n\t{e.__traceback__.tb_frame}')
            response = JsonResponse(data = {"Message": str(e)}, status=status.HTTP_417_EXPECTATION_FAILED)
            if 'deadlocked' in str(e):
                logger.debug(f'Caught Deadlock error: {str(e)}')
                await pauseOnDeadlock('approvedEntries', inputData['id'])
            raise e # retry is handled by celery broker 
    await sync_to_async(taskResult)(response.content, inputData, 'putBatchEntries')
    return response

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def batchEntriesWrapper(self, inputData: dict):
    '''
    Function Description: 
        Wraps the async function putBatchEntries in a normal Celery task. 

    Param: 
        inputData(dict): contains the the body of the request sent to the main server in the updateTimesheet function    
    '''
    try:
        loop = asyncio.get_event_loop()
        result =  loop.run_until_complete(putBatchEntries(inputData))
        logger.info(result)
        return result
    except Exception as e:
        logger.warning(f'Task failed with exception {str(e)} at ({e.__traceback__.tb_lineno}). Retrying...')
        self.retry(exc = e)



def deleteCategory(newCategories):
    '''
    Function Description: 
        Checks all categories in the database against the most recent pull and deletes stall categories.

    Param: 
        newCategories([dict]): List of category json data recently pulled from clockify  
    
    Returns: 
        deleted(int): Number of categories deleted from the database  
    '''
    
    logger = setup_background_logger(loggerLevel)
    deleted = 0
    categories = Category.objects.all()
    for category in categories:
        if check_category_for_deletion(category.id, newCategories):
            logger.info('Found Stale Cateogory')
            category.delete
            deleted += 1
    return deleted 

@csrf_exempt
async def retryExpenses(request: ASGIRequest):   
    '''
    Function Description: 
        Handles a FK constraint on Expenses by updating the Category table and redirecting back to the expense function 

        Result of the task fumction is stored in the database table 'BackGroundTaskDjango'. Transactions are not atomic 

    Param: 
        request(ASGIRequest): contains the the body of the request sent to the main server   
    
    Returns: 
        response(JsonResponse): Required return value that is not accessed later
    '''
    logger = setup_background_logger(loggerLevel)
    if request.method == 'POST':
        try:
            caller = 'Pulling Expense Category and trying again'
            logger.info(caller)
            inputData = request.POST
            logger.debug(reverseForOutput(inputData))
            
            categories = getCategories(inputData['workspaceId'], 1) #new data from clockify 
            
            logger.info('Checking for stale Categories... ')
            deleteCategoryAsync = sync_to_async(deleteCategory)
            deleted = await deleteCategoryAsync(categories['categories']) 
            logger.info(f'Deleted {deleted} Categories')
            logger.debug(reverseForOutput(categories))
            
            def pushCategories(category:dict):
                try: 
                    try: #try update otherwise insert for Categories 
                        categoryInstanece = Category.objects.get(pk=category["id"])
                        serializer = CategorySerializer(data= category, instance=categoryInstanece)
                        logger.info(f'Existing Category... Updatiing')
                    except Category.DoesNotExist:
                        serializer = CategorySerializer(data = category)
                        logger.info(f'New Category... Inserting')
                    if serializer.is_valid():
                        serializer.save()
                        logger.info(f'Changes Saved')
                        return 1
                    else:
                        logger.error(serializer.error_messages)
                        raise ValidationError(f'Could not serialize data: \n{reverseForOutput(serializer.errors)}')
                except Exception as e: 
                    logger.error(f'({e.__traceback__.tb_lineno}) Retry Expenses - ({str(e)})')
                    raise e
            
            tasks = []
            pushCategoriesAsync = sync_to_async(pushCategories, thread_sensitive=False)

            for i in range(0,len(categories['categories'])): # updates/inserts all Expense categories async  
                tasks.append(
                    pushCategoriesAsync(categories['categories'][i]) # returns coroutine function 
                )
            await asyncio.gather(*tasks) # calling all async 
            logger.info(f'Categories updated')
            headers = {
                'Clockify-Signature': 'CiLrAry1UiEZb4OnPmX67T8un5GuYw24'
            }
            url =  'http://localhost:8000/HpClockifyApi/newExpense' # host url of main server 
            requests.post(url=url, data=inputData, headers=headers)
            response = JsonResponse(data = 'Retry Expense Event Completed Succesfully', status=status.HTTP_201_CREATED, safe = False)
            taskResult.delay(response.content, inputData, caller)
            return response
        except Exception as e:
            response = JsonResponse(data = {'Message': f'({e.__traceback__.tb_lineno}) - {str(e)}'}, status=status.HTTP_400_BAD_REQUEST, safe = False)
            logger.critical(response.content.decode('utf-8'))
            taskResult.delay(response.content, inputData, caller)
            return response
    
    else:
        response =  JsonResponse(
            data={
                'Message': 'Method Not Suported'
            }, status= status.HTTP_405_METHOD_NOT_ALLOWED
        )
        taskResult.delay(response.content, inputData, caller)
        return response


@csrf_exempt
async def approvedExpenses(request:ASGIRequest):
    logger = setup_background_logger()
    caller = 'Approved Expense function called'
    logger.info(caller)
    if request.method == 'POST':
        inputData = bytes_to_dict(request.body)
        logger.debug(f'InputData\n{reverseForOutput(inputData)}')
        key = getApiKey()
        timeId = inputData.get("id")
        workspaceId = inputData.get('workspaceId')
        stat = inputData.get('status').get('state') or None

        if stat =='APPROVED':
            allExpenses = await getDataForApproval(workspaceId, key, timeId, stat, expenseFlag=True)
            if len(allExpenses) == 0:
                logger.warning('No Content. Is this expected?')
                response =  JsonResponse(data = {f'Message': f'No Expenes for timesheet {timeId}'}, status=status.HTTP_204_NO_CONTENT, safe=False)
                taskResult.delay(response.content, inputData, caller)
                return response
            def syncUpdateExpense(expense):
                #refactoring 
                expense['categoryId'] = expense['category']["id"]
                expense[ 'projectId'] = expense['project']["id"]
                expense['timesheetId'] = expense['approvalRequestId']
                try:
                    try:
                        approvalID = expense['approvalRequestId'] if expense['approvalRequestId'] is not None else timeId
                        expenseObj = Expense.objects.get(id=expense["id"], workspaceId = workspaceId)

                        serializer = ExpenseSerializer(instance=expenseObj, data=expense)
                        logger.info('Updating Expense...')
                    except Expense.DoesNotExist:
                        serializer = ExpenseSerializer(data=expense)
                        logger.warning(f'Creating new Expense on timesheet {timeId}')
                    if serializer.is_valid():
                        serializer.save()
                        logger.info(f'UpdateExpense on timesheet({timeId}): EX-{expense["id"]} 202 ACCEPTED')
                        logger.info(reverseForOutput(expense))
                        return serializer.validated_data
                    else:
                        logger.error(serializer.error)
                        raise ValidationError(serializer.errors)
                except Exception as e:
                    logger.error(f'{str(e)} at line {e.__traceback__.tb_lineno} in \n\t{e.__traceback__.tb_frame}') 
                    raise  e
                
            asyncUpdateExpense = sync_to_async(syncUpdateExpense)
            tasks = []
            for expense in allExpenses:
                tasks.append(
                    asyncUpdateExpense(expense)
                )
            try:
                await asyncio.gather(*tasks)
                logger.info(f'Expense added for timesheet {timeId}') 
                response =  JsonResponse(data = 'Approved Expense Opperation Completed Succesfully', status=status.HTTP_201_CREATED, safe=False)
                taskResult.delay(response.content, inputData, caller)
                return response
            except Exception as e:
                logger.error(f'{str(e)} at line {e.__traceback__.tb_lineno} in \n\t{e.__traceback__.tb_frame}')
                response =  JsonResponse(data = None, status=status.HTTP_417_EXPECTATION_FAILED, safe = False)
                taskResult.delay(response.content, inputData, caller)
                return response

        else:
            logger.info(f'UpdateExpense on timesheet({timeId}): Update on Pending or Withdrawn timesheet not necessary: {stat}  406 NOT_ACCEPTED    ')
            response =  JsonResponse(data = None, status=status.HTTP_204_NO_CONTENT, safe = False)
            taskResult.delay(response.content, inputData, caller)
            return response
    else:
        response = JsonResponse(data=None, status = status.HTTP_405_METHOD_NOT_ALLOWED, safe = False)
        taskResult.delay(response.content, inputData, caller)
        return response

def postThreadLemEntryTask(inputData: dict):
    logger = setup_background_logger()
    try:
        inputData["workerId"] = LemWorker.objects.get(empId = inputData['empId'], roleId= inputData['roleId']).pk  #refactoring
        inputData["_id"] = hash50(50 ,inputData['lemId'], inputData['workerId'], inputData['roleId'])
        logger.debug(inputData["_id"])
        logger.debug(reverseForOutput(inputData))
        serializer = LemEntrySerializer(data=inputData)
        if serializer.is_valid():
            serializer.save() 
            logger.info("Succsesfully saved Lem Entry")
            return True
        else:
            for key, value in serializer.errors.items():
                logger.info(dumps({'Error Key': key, 'Error Value': value}, indent =4))
            raise ValidationError(serializer.error_messages)
    except Exception as e: 
            logger.error(f"({e.__traceback__.tb_lineno}) - {str(e)} in {e.__traceback__.tb_frame}")
            raise e

@csrf_exempt
async def lemEntrytTask(request: ASGIRequest): 
    logger = setup_background_logger()
    try:
        logger.info('Inserting Lem Entry Information')

        inputData = bytes_to_dict(request.body)
        logger.debug(inputData)
        logger.debug(type(inputData) )
        if request.method == 'POST':
            post = sync_to_async(postThreadLemEntryTask, thread_sensitive=False)
            await post(inputData)
            return JsonResponse(data=inputData, status= status.HTTP_201_CREATED)
        else: #do this later if needed
            return JsonResponse(data='Feture Not Extended', status = status.HTTP_510_NOT_EXTENDED, safe=False)
    except ValidationError as v:
            return JsonResponse(data="Invalid Request. Revew Selections and try again. Contact admin if problem persists", status =status.HTTP_400_BAD_REQUEST, safe=False) 
    except utils.IntegrityError as c:
            if "PRIMARY KEY constraint" in str(c):
                logger.error(reverseForOutput(inputData))
                raise(utils.IntegrityError("Server is trying to insert a douplicate record. Contact Adin if problem persists "))
            return JsonResponse(data = inputData, status= status.HTTP_409_CONFLICT, safe = False)
    except Exception as e:
        response = JsonResponse(data=f'A problem occured while handling your request. If error continues, contact admin \n({e.__traceback__.tb_lineno}): {str(e)} in {e.__traceback__.tb_frame}', status=status.HTTP_501_NOT_IMPLEMENTED, safe = False)
        logger.error(response.content)
        return response
    
