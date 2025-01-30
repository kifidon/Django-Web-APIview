from django.http import JsonResponse
from rest_framework import status
from .tasks import *
from Utilities.views import setup_server_logger
from django.core.handlers.asgi import ASGIRequest

events = {
            'user': UserEvent.s(wkSpaceName = 'Hill Plain'),
            'client': ClientEvent.s(wkSpaceName = 'Hill Plain'),
            'project': ProjectEvent.s(wkSpaceName = 'Hill Plain'),
            'policy': PolicyEvent.s(wkSpaceName = 'Hill Plain'),
            'timesheet': TimesheetEvent.s(wkSpaceName = 'Hill Plain'),
            'timeoff': TimeOffEvent.s(wkSpaceName = 'Hill Plain'),
            'holiday': HolidayEvent.s(wkSpaceName = 'Hill Plain'),
        }

'''
Asynchronously selects and executes an event based on the specified input event type.

Args:
    event (str, optional): The type of event to execute. Options include:
        'user', 'client', 'project', 'policy', 'timesheet', 'timeoff', 
        'holiday', and 'userGroup'. Defaults to None, which calls `main()`.

Process:
    - Initializes specific event classes for each event type with a workspace 
      name of "Hill Plain".
    - Uses `asyncio.gather` to run the selected event asynchronously.
    - Logs results and the data type of the output.

Returns:
    list: A list containing the result of the specified event, or an exception 
    if any occurred during execution.

Raises:
    Logs an error with traceback details if an exception occurs, then re-raises it.
'''
def QuickBackup(request: ASGIRequest, event = None):
    logger = setup_server_logger()
    try:

        results = []
        if event is None:
            results = mainBackup()
        else:
            func =  events.get(event)
            if func is None:
                raise ValueError('Invalid event type')
            results.append(func.delay().id)
        logger.info(f'Submit Jobs:  {results}')
        response = JsonResponse({'status': 'success', 'message': 'Backup job submitted', 'data': results}, status = status.HTTP_200_OK)
    except Exception as e:
        response = JsonResponse({'status': 'error', 'message': str(e)}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
        logger.error(f"{e.__traceback__.tb_lineno} - {str(e)}")
        raise e
    taskResult.delay(response.content, {}, 'QuickBackup')
    return response
    
def detailedTimesheetBackup(request:ASGIRequest, offset = None| str):
    logger = setup_server_logger()
    logger.info(f'Submitting Timesheet backup with offset {offset}')
    TimesheetEvent.delay(offset=int(offset))
    response = JsonResponse({'status': 'success', 'message': 'Backup job submitted'}, status = status.HTTP_200_OK)
    return response

@shared_task
def BankedHrs(request= None| ASGIRequest ):
    logger = setup_background_logger()
    '''
    Function Description: 
        Calls pull request functions from the databse to update the banked hours ballance in clockify. 
    Param: 
        request(ASGIRequest): Request sent to endpoint from client 
    
    Returns: 
        response(Response): contains Payroll Report File to be directly uploaded into ACC
    '''
    BankedHrsTask()
    return JsonResponse(data='Operation Completed', status=status.HTTP_200_OK, safe=False)
    

def UpdateSalaryVacation(request = None| ASGIRequest):
    '''
    Function Description: 
        Calls pull request functions from the databse to update the vacation hours ballance in clockify. 
    Param: 
        request(ASGIRequest): Request sent to endpoint from client 
    
    Returns: 
        response(Response): contains Payroll Report File to be directly uploaded into ACC
    '''
    SalaryVacationTask.delay()
    return JsonResponse(data='Operation Completed', status=status.HTTP_200_OK, safe=False)
    
