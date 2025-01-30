from ast import Str
from celery import shared_task
from json import loads
from .models import BackGroundTaskResult
from HillPlainAPI.Loggers import setup_background_logger, setup_server_logger
from datetime import datetime
import pytz
from Utilities.clockify_util import ClockifyPushV3
from Utilities.views import sqlConnect, cleanUp
import asyncio
import datetime
from Clockify.models import Employeeuser

from Utilities.clockify_util.ClockifyScheduledTasks import BankedTime, updateSalaryVacation


@shared_task
def UserEvent(wkSpaceName = 'Hill Plain'):
    logger = setup_server_logger()
    logger.info("Executing scheduled or background task: User")
    logger = setup_background_logger()
    logger.info('User Event Called')
    wid = ClockifyPushV3.getWID(wkSpaceName)
    result = ClockifyPushV3.pushUsers(wid)
    return result

@shared_task
def ClientEvent(wkSpaceName = 'Hill Plain'):
    
    logger = setup_server_logger()
    logger.info("Executing scheduled or background task: Client")
    logger = setup_background_logger()
    logger.info('Client Event Called')
    wid = ClockifyPushV3.getWID(wkSpaceName)
    cursor , conn = sqlConnect()
    logger.debug('Transfering to handler function')
    result = ClockifyPushV3.pushClients(wid ,conn, cursor)
    logger.info(result)
    cleanUp(conn=conn, cursor=cursor)
    return result

@shared_task
def ProjectEvent(wkSpaceName = 'Hill Plain'):
    logger = setup_server_logger()
    logger.info("Executing scheduled or background task: Project")
    logger = setup_background_logger()
    logger.info('Project Event Called')
    wid = ClockifyPushV3.getWID(wkSpaceName)
    result = ClockifyPushV3.pushProjects(wid)
    logger.info(result)
    return result

@shared_task
def PolicyEvent(wkSpaceName = 'Hill Plain'):
    logger = setup_server_logger()
    logger.info("Executing scheduled or background task: Policy")
    logger = setup_background_logger()
    logger.info('Policy Event Called')
    wid = ClockifyPushV3.getWID(wkSpaceName)
    cursor , conn = sqlConnect()
    result = ClockifyPushV3.pushPolicies(wid, conn, cursor)
    logger.info(result)
    cleanUp(conn=conn, cursor=cursor)
    return result

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def TimesheetEvent(self, wkSpaceName = 'Hill Plain', offset = 1):# , status = ['APPROVED', 'PENDING', 'WITHDRAWN_APPROVAL']):
    try:
        logger = setup_server_logger()
        logger.info("Executing scheduled or background task: Timesheet")
        logger = setup_background_logger()
        logger.info('Timesheet Event Called')
        wid = ClockifyPushV3.getWID(wkSpaceName)
        result = ClockifyPushV3.pushTimesheets(wid, offset)
        logger.debug(f"pushTimesheets Result: {result}")
        logger.info(result)
        return result 
    except Exception as e:
        logger.warning(f'Task failed with exception {str(e)}. Retrying...')
        self.retry(exc = e)
@shared_task
def TimeOffEvent(wkSpaceName = 'Hill Plain'):
    logger = setup_server_logger()
    logger.info("Executing scheduled or background task: TimeOff")
    logger = setup_background_logger()
    logger.info('Timeoff Event Called')
    wid = ClockifyPushV3.getWID(wkSpaceName)
    logger.debug(f"WID: {wid}")
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(ClockifyPushV3.pushTimeOff(wid))
    logger.debug(result)
    return result

@shared_task
def HolidayEvent(wkSpaceName = 'Hill Plain'):
    logger = setup_server_logger()
    logger.info("Executing scheduled or background task: Holiday")
    logger = setup_background_logger()
    logger.info('Holiday Event Called')
    wid = ClockifyPushV3.getWID(wkSpaceName)
    cursor , conn = sqlConnect()
    result = ClockifyPushV3.pushHolidays(wid, conn, cursor)
    logger.info(result)
    cleanUp(conn=conn, cursor=cursor)
    return result

@shared_task
def CalendarEvent():
    logger = setup_server_logger()
    logger.info("Executing scheduled or background task: Calendar")
    logger = setup_background_logger()
    cursor, conn = sqlConnect()
    logger.info(f"Calendar event Called")
    result = ClockifyPushV3.updateCalendar(str(datetime.datetime.now().year + 1), conn, cursor)
    return result


def mainBackup():
    logger = setup_server_logger()
    logger.info("Executing scheduled or background task: ALL")
    logger = setup_background_logger()
    logger.info('Main Backup Event Called')
    tasks = []
    tasks.append(ClientEvent.delay()),
    tasks.append(UserEvent.delay()),
    tasks.append(ProjectEvent.delay()),
    tasks.append(PolicyEvent.delay()),
    tasks.append(TimesheetEvent.delay()),
    tasks.append(TimeOffEvent.delay()),
    tasks.append(HolidayEvent.delay()),
    tasks.append(CalendarEvent.delay())
    return tasks

        
        
'''
Saves the result of a background task to the BackGroundTaskResult table.

Args:
    response (JsonResponse): The response object containing the task's status and message.
    inputData: The data related to the task being saved.
    caller (str): Identifier for the source or function that initiated the task.

Logs the task result and stores it with a timestamp in the database.
'''
@shared_task
def taskResult(response: str, inputData:dict, caller: str):
    decoded = response.decode('utf-8')
    response = loads(decoded)
    if not isinstance(response, dict):
        response = {}
    
    logger = setup_server_logger()
    logger.info("Executing scheduled or background task")
    logger = setup_background_logger()
    logger.info('Saving task result')
    timezone = pytz.timezone('America/Denver')
    current_time = datetime.datetime.now(timezone)

    # Format the time in the required format
    formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S.%f%z')
    BackGroundTaskResult.objects.create(
        status_code = response.get("status_code", "111"),
        message = decoded or None,
        data = inputData,
        caller = caller,
        time = formatted_time
    )

@shared_task
def SalaryVacationTask():
    '''
    Function Description: 
        Calls pull request functions from the databse to update the vacation hours ballance in clockify. 
    Param: 
        request(ASGIRequest): Request sent to endpoint from client 
    
    Returns: 
        response(Response): contains Payroll Report File to be directly uploaded into ACC
    '''
    logger = setup_background_logger()
    logger.info(f'Update Salary ')
    try:
        cursor, conn = sqlConnect()
        users = list(Employeeuser.objects.filter(hourly=0, status ='ACTIVE'))
        for usr in users:
            update = updateSalaryVacation(usr.id, cursor)
            logger.info(f"{usr.name}: {update}")
        cleanUp(conn, cursor)
    except Exception as e:
        logger.error(f'({e.__traceback__.tb_lineno}){str(e)} in {e.__traceback__.tb_frame}') 


@shared_task
def BankedHrsTask():
    logger = setup_background_logger()
    '''
    Function Description: 
        Calls pull request functions from the databse to update the banked hours ballance in clockify. 
    Param: 
        request(ASGIRequest): Request sent to endpoint from client 
    
    Returns: 
        response(Response): contains Payroll Report File to be directly uploaded into ACC
    '''
    logger.info(f'BankedHours Task! ')
    try:
        BankedTime()
    except Exception as e:
        logger.error(f'{str(e)}')
        