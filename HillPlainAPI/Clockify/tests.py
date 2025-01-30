import json
from io import BytesIO
import re
from unittest.mock import patch, AsyncMock, MagicMock
from django.test import TestCase
from django.urls import reverse
from django.http import JsonResponse
from Clockify.models import Workspace, Project, Employeeuser 
import Clockify.models
import Clockify.serializers
import Clockify.tasks
from Clockify.views import EntryView, TimeoffRequestsView, TimesheetsView
import Clockify.views
import Clockify
from asgiref.sync import async_to_sync
from django.core.handlers.asgi import ASGIRequest

from httpx import ASGITransport

def loadData():
    workspace = Workspace.objects.create(id="65c249bfedeea53ae19d7dad", name='Hill Plain')
    client = Clockify.models.Client.objects.create(id = '65c25ae977682a2076d96d49', email = None,
        address = None,
        name = "Hill Plain Internal",
        workspace = workspace
    )
    project = Project.objects.create(id = "65c262c0edeea53ae1a27b84",
        name = "000-000 - Overhead (Non Billable)",
        title = "Overhead (Non Billable)",
        code = "000-000",
        clientId = client,
        workspaceId = workspace,
    )
    user = Employeeuser.objects.create(
        id = "65bd6a6077682a20767a6c0b",
        email = "timmy.ifidon@hillplain.com",
        name = "Timmy Ifidon",
        status = "ACTIVE",
        role = "Co-op Student ",
        manager = "Shawna Applejohn",
        start_date = "2024-01-03",
        end_date = None,
        hourly = 1,
        Truck = "0",
        truckDetails = None
    )

def buildRequest(url, secret, data):
    headers = [
            (b"content-type", b"application/json"),
            (b"Clockify-Signature", f"{secret}".encode("utf-8"))
    ]
    scope = {
        "type": "http",
        "method": "POST",
        "path": url,
        "headers": headers, 
    }
    body_file = BytesIO(json.dumps(data).encode('utf-8'))
    return ASGIRequest(scope, body_file)

class EntryViewTestCase(TestCase):
    
    def setUp(self):
        loadData()
        self.url = "http://localhost:8000"+ reverse("clockifyEntry")
        self.secret = 'e2kRQ3xauRrfFqkyBMsgRaCLFagJqmCE' #newEntry 
        self.secret2 = 'Ps4GN6oxDKYh9Q33F1BULtCI7rcgxqXW' #updateEntry 
        self.secret3 = '0IQNBiGEAejNMlFmdQc8NWEiMe1Uzg01' #DeleteEntry 
        self.valid_data = {
            "id": "675ad59b3693cd4651b63441",
            "description": "Mapping models from Web Application to database. Test database was emtpy which caused all test cases to fail. Once mapped, tests began to pass ",
            "userId": "65bd6a6077682a20767a6c0b",
            "billable": False,
            "projectId": "65c262c0edeea53ae1a27b84",
            "timeInterval": {
                "start": "2024-12-11T23:00:00Z",
                "end": "2024-12-12T03:00:00Z",
                "duration": "PT4H"
            },
            "workspaceId": "65c249bfedeea53ae19d7dad",
            "isLocked": False,
            "hourlyRate": None,
            "costRate": None,
            "customFieldValues": [],
            "type": "REGULAR",
            "kioskId": None,
            "approvalStatus": None,
            "projectCurrency": None,
            "currentlyRunning": False,
            "project": {
                "name": "000-000 - Overhead (Non Billable)",
                "clientId": "65c25ae977682a2076d96d49",
                "workspaceId": "65c249bfedeea53ae19d7dad",
                "billable": False,
                "estimate": {
                    "estimate": "PT0S",
                    "type": "AUTO"
                },
                "color": "#03A9F4",
                "archived": False,
                "clientName": "Hill Plain Internal",
                "duration": "PT19471H16M48S",
                "note": "",
                "activeEstimate": "NONE",
                "timeEstimate": {
                    "includeNonBillable": True,
                    "estimate": 0,
                    "type": "AUTO",
                    "resetOption": None
                },
                "budgetEstimate": None,
                "estimateReset": None,
                "id": "65c262c0edeea53ae1a27b84",
                "public": True,
                "template": False
            },
            "task": None,
            "user": {
                "id": "65bd6a6077682a20767a6c0b",
                "name": "Timmy Ifidon",
                "status": "ACTIVE"
            },
            "tags": []
        }
        self.request = buildRequest(self.url, self.secret, self.valid_data)
        
        
    @patch('Clockify.views.taskResult.delay')  # Mocking saveTaskResult function
    def testValidPost(self, mock_save_task_result: AsyncMock):
        """Test a valid dispatch request where authentication passes."""
        mock_save_task_result.return_value =None 

        response = async_to_sync(EntryView.as_view())(self.request)

        mock_save_task_result.assert_called_once()

        # Ensure the response status code is as expected
        self.assertEqual(response.status_code, 202)

    @patch('Clockify.views.taskResult.delay')  # Mocking saveTaskResult function
    @patch('Clockify.views.aunthenticateRequest')  # Mocking failed authentication
    def test_dispatch_invalid_request(self, mock_authenticate: MagicMock, mockTaskResult: MagicMock):
        """Test a dispatch request where authentication fails."""
        mock_authenticate.return_value = False
        mockTaskResult.return_value = None
        
        response = async_to_sync(EntryView.as_view())(self.request)

        # Check if processPostEntry was not called because of failed authentication
        mockTaskResult.assert_called_once()

        # Ensure the response status code is 423 (Locked) for invalid security
        self.assertEqual(response.status_code, 423)


    @patch('Clockify.views.taskResult.delay')  # Mocking saveTaskResult function
    def testValidUpdate(self, mockTestResult: MagicMock):
        """Test a valid update request."""
        # Place the data in test database 
        mockTestResult.return_value = None
        
        view = Clockify.views.EntryView()
        self.assertTrue(view.processPostEntry(self.valid_data))
        
        self.request = buildRequest(self.url, self.secret2, self.valid_data)
        response = async_to_sync(EntryView.as_view())(self.request)
        
        mockTestResult.assert_called()
        self.assertEqual(response.status_code, 202)
        
    @patch('Clockify.views.taskResult.delay')  # Mocking saveTaskResult function
    def testDelete(self, mockTestResult: MagicMock):
        """Test a valid delete request."""
        mockTestResult.return_value = None
        view = Clockify.views.EntryView()
        self.assertTrue(view.processPostEntry(self.valid_data))
        
        self.request = buildRequest(self.url, self.secret3, self.valid_data)
        response = async_to_sync(EntryView.as_view())(self.request)
        
        mockTestResult.assert_called()
        self.assertEqual(response.status_code, 202)
        
    @patch('Clockify.views.taskResult.delay')  # Mocking saveTaskResult function
    def test_valid_post_foreign_key(self, mockTestResult: MagicMock):
        """Test a valid post request with missing invalid or missing project is handled properly"""
        mockTestResult.return_value =None 
       
        self.valid_data['project']["id"] = "Invalid Projcet"

        self.request = buildRequest(self.url, self.secret, self.valid_data)
        response = async_to_sync(EntryView.as_view())(self.request)
        
        mockTestResult.assert_called_once()
        self.assertEqual(response.status_code, 202)



    @patch("Clockify.views.EntryView.processPostEntry")
    @patch("Clockify.views.pauseOnDeadlock")
    @patch('Clockify.views.taskResult.delay')  # Mocking saveTaskResult function
    def test_deadlock_wait(self, mockTaskResult: MagicMock, mockPauseOnDeadlock: AsyncMock, mockProcessPost: MagicMock):
        """Test a deadlock wait and retry."""
        mockTaskResult.return_value =None 
        mockPauseOnDeadlock.return_value = None
        mockProcessPost.side_effect = Exception(' this exception contains the words deadlocked inside the str')
       
        response = async_to_sync(EntryView.as_view())(self.request)

        #asert Deadlock was waited and tried again
        mockPauseOnDeadlock.assert_awaited()

        mockTaskResult.assert_called_once()
        # Ensure the response status code is as expected
        self.assertEqual(response.status_code, 500)

class TimesheetViewTestCase(TestCase):

    def setUp(self):
        loadData()
        self.url = "http://localhost:8000"+ reverse("clockifyTimesheet")
        self.secret = 'Qzotb4tVT5QRlXc3HUjwZmkgIk58uUyK' #insert 
        self.secret2 = 'me1lD8vSd5jqmBeaO2DpZvtQ2Qbwzrmy' #update  
        self.valid_data = {
            "id": "675ad47779c3ba2c2d6a9d5e",
            "workspaceId": "65c249bfedeea53ae19d7dad",
            "dateRange": {
                "start": "2024-12-01T07:00:00Z",
                "end": "2024-12-08T06:59:59Z"
            },
            "owner": {
                "userId": "65bd6a6077682a20767a6c0b",
                "userName": "Timmy Ifidon",
                "timeZone": "America/Edmonton",
                "startOfWeek": "SUNDAY"
            },
            "status": {
                "state": "PENDING",
                "updatedBy": "65bd6a6077682a20767a6c0b",
                "updatedByUserName": "Timmy Ifidon",
                "updatedAt": "2024-12-12T12:17:59Z",
                "note": ""
            },
            "creator": {
                "userId": "65bd6a6077682a20767a6c0b",
                "userName": "Timmy Ifidon",
                "userEmail": "timmy.ifidon@hillplain.com"
            },
            "approvalStatuses": {}
        }
        self.request = buildRequest(self.url, self.secret, self.valid_data)

    @patch('Clockify.views.taskResult.delay')  # Mocking saveTaskResult function
    @patch('Clockify.views.batchEntriesWrapper.delay')  
    def testValidPost(self, mockBatchEntries: MagicMock, mockTaskResult: MagicMock):
        """Test a valid request where entries are sent to the background with succesful execution of request"""
        mockBatchEntries.return_value = None
        mockTaskResult.return_value = None

        response = async_to_sync(TimesheetsView.as_view())(self.request)

        mockTaskResult.assert_called_once()
        mockBatchEntries.assert_called_once()
        self.assertEqual(response.status_code, 202)

    @patch('Clockify.views.batchEntriesWrapper.delay')
    @patch('Clockify.tasks.processPut')
    @patch('Clockify.tasks.getDataForApproval')
    @patch('Clockify.views.taskResult.delay')  # Mocking saveTaskResult function
    @patch('Clockify.tasks.taskResult')  # Mocking saveTaskResult function
    def testPutOnTimesheet(self, mockCreateTaskResult: MagicMock, mockTaskResult: MagicMock, mockGetData: AsyncMock, mockProcessPut: MagicMock, mockBatchEntries: MagicMock):
        """Test a valid request where entries are sent to the background and succesful execution of request"""
        mockCreateTaskResult.return_value = None
        mockTaskResult.return_value = None
        mockGetData.return_value = [1, 2, 3] # Dummy list of entries to be processed
        mockProcessPut.return_value = None
        mockBatchEntries.return_value = None

        task = Clockify.views.batchEntriesWrapper(self.valid_data)
        
    
        response = async_to_sync(TimesheetsView.as_view())(self.request)

        mockCreateTaskResult.assert_called_once()
        mockTaskResult.assert_called()
        mockGetData.assert_called_once()
        mockProcessPut.assert_called()
        
        self.assertEqual(response.status_code, 202)
        self.assertEqual(task.status_code , 201)

'''
# class EmpUserViewTestCase(TestCase):
    
#     def setUp(self):
#         loadData()
#         self.client = Client()
#         self.url = "http://localhost:8000"+ reverse("Users")
#         self._secret ={ "update": 'TSnab31ks1Ml1oXkZHMIzp7R33SRSedz', 
#                         "insert": 'v9otRjmoOBTbwkf6IaBJ4VUgRGC8QU6V'  ,
#                         "activate": 'Z9m05F1vt873wHG6hNAHok6l5YnJWmlM',
#                         "deactivate": 'JtyuoJ1ds3tSeXB9vyPIHjRCmb0vmmDx'
#         } 
#         self.headers = {
#             'Clockify-Signature': f'{self._secret['update']}'
#         }
#         self.valid_data ={
#             "id": "65c253aeffbbb676c5e05ff0",
#             "email": "chelsea.stepien@hillplain.com",
#             "name": "Chelsea Stepien",
#             "profilePicture": "https://img.clockify.me/no-user-image.png",
#             "settings": {
#                 "weekStart": "SUNDAY",
#                 "timeZone": "America/Edmonton",
#                 "timeFormat": "HOUR12",
#                 "dateFormat": "MM/DD/YYYY",
#                 "sendNewsletter": False,
#                 "weeklyUpdates": False,
#                 "longRunning": False,
#                 "scheduledReports": False,
#                 "approval": False,
#                 "pto": False,
#                 "alerts": False,
#                 "reminders": False,
#                 "onboarding": False,
#                 "timeTrackingManual": False,
#                 "summaryReportSettings": {
#                     "group": "Project",
#                     "subgroup": "Time Entry"
#                 },
#                 "isCompactViewOn": False,
#                 "dashboardSelection": "ME",
#                 "dashboardViewType": "PROJECT",
#                 "dashboardPinToTop": False,
#                 "projectListCollapse": 50,
#                 "collapseAllProjectLists": False,
#                 "groupSimilarEntriesDisabled": False,
#                 "myStartOfDay": "09:00",
#                 "darkTheme": False,
#                 "projectPickerSpecialFilter": False,
#                 "lang": "EN",
#                 "multiFactorEnabled": False,
#                 "scheduling": False,
#                 "showOnlyWorkingDays": False,
#                 "theme": "DEFAULT"
#             },
#             "userCustomFields": [
#                 {
#                     "customFieldId": "664d0d0a6a8fa06c786a886e",
#                     "value": "Director",
#                     "name": "Role",
#                     "type": "DROPDOWN_SINGLE"
#                 },
#                 {
#                     "customFieldId": "664d0d56a17be2283ae908ec",
#                     "value": "2023-09-25",
#                     "name": "Start Date",
#                     "type": "TXT"
#                 },
#                 {
#                     "customFieldId": "66636c8285def31fcde9e5c3",
#                     "value": False,
#                     "name": "Truck",
#                     "type": "CHECKBOX"
#                 },
#                 {
#                     "customFieldId": "66c76868b576ce03a631b832",
#                     "value": "0",
#                     "name": "Rate Type",
#                     "type": "DROPDOWN_SINGLE"
#                 },
#                 {
#                     "customFieldId": "66c7731b23ff85648debc3a9",
#                     "value": "Ahmad Tadbir",
#                     "name": "Reporting Manager",
#                     "type": "DROPDOWN_SINGLE"
#                 },
#                 {
#                     "customFieldId": "66d8cf6576240c2fd6f6db89",
#                     "value": "2024-05-28",
#                     "name": "End Date",
#                     "type": "TXT"
#                 }
#             ]
#         }
    
#     @patch('Clockify.views.saveTaskResult')
#     @patch('Clockify.views.asave')
#     def testUpdateKeyActiviy(self, mockASave: AsyncMock, mockSaveTask: AsyncMock ):
#         """Test a valid update secret key """
#         mockASave.return_value = None 
#         mockSaveTask.return_value = None
#         self.headers = {
#             'Clockify-Signature': f'{self._secret['update']}'
#         }
#         # Simulate the POST request
#         response = self.client.post(
#             self.url,
#             data=json.dumps(self.valid_data),
#             headers=self.headers,
#             content_type='application/json',
#         )

#         mockASave.assert_awaited_once()
#         self.assertEqual(response.status_code, 201)

#     @patch('Clockify.views.saveTaskResult')
#     @patch('Clockify.views.asave')
#     def testInsertKeyActiviy(self, mockASave: AsyncMock, mockSaveTask: AsyncMock ):
#         """Test a valid insert secret key """
#         mockASave.return_value = None 
#         mockSaveTask.return_value = None
#         self.headers = {
#             'Clockify-Signature': f'{self._secret['insert']}'
#         }
#         # Simulate the POST request
#         response = self.client.post(
#             self.url,
#             data=json.dumps(self.valid_data),
#             headers=self.headers,
#             content_type='application/json',
#         )

#         mockASave.assert_awaited_once()
#         self.assertEqual(response.status_code, 201)

#     @patch('Clockify.views.saveTaskResult')
#     @patch('Clockify.views.asave')
#     def testActivatetKeyActiviy(self, mockASave: AsyncMock, mockSaveTask: AsyncMock ):
#         """Test a valid activate secret key """
#         mockASave.return_value = None 
#         mockSaveTask.return_value = None
#         self.headers = {
#             'Clockify-Signature': f'{self._secret['activate']}'
#         }
#         # Simulate the POST request
#         response = self.client.post(
#             self.url,
#             data=json.dumps(self.valid_data),
#             headers=self.headers,
#             content_type='application/json',
#         )

#         mockASave.assert_awaited_once()
#         self.assertEqual(response.status_code, 201)

#     @patch('Clockify.views.saveTaskResult')
#     @patch('Clockify.views.asave')
#     def testDeactivatetKeyActiviy(self, mockASave: AsyncMock, mockSaveTask: AsyncMock):
#         """Test a valid deactivate secret key """
#         mockASave.return_value = None 
#         mockSaveTask.return_value = None
#         self.headers = {
#             'Clockify-Signature': f'{self._secret['deactivate']}'
#         }
#         # Simulate the POST request
#         response = self.client.post(
#             self.url,
#             data=json.dumps(self.valid_data),
#             headers=self.headers,
#             content_type='application/json',
#         )

#         mockASave.assert_awaited_once()
#         self.assertEqual(response.status_code, 201)
    
#     @patch('Clockify.views.saveTaskResult')
#     @patch('Clockify.views.asave')
#     def testInvalidActiviy(self, mockASave: AsyncMock, mockSaveTask: AsyncMock ):
#         """Test an Invalid secret key """
#         mockASave.return_value = None 
#         mockSaveTask.return_value = None
#         self.headers = {
#             'Clockify-Signature': f'INVALID'
#         }
#         # Simulate the POST request
#         response = self.client.post(
#             self.url,
#             data=json.dumps(self.valid_data),
#             headers=self.headers,
#             content_type='application/json',
#         )

#         mockASave.assert_not_awaited()
#         self.assertEqual(response.status_code, 423)
'''        

class TimeOffViewTestCase(TestCase):
    def setUp(self):
        loadData()
        self.url = "http://localhost:8000"+ reverse("TimeOff")
        self._secret={"update": "W7Lc7BGRq1wvIC0eQS5Bik5m05JF8RkZ",
                      "create": "I7DOlIagZOjUBhHS0HObcvyaBiz7covJ", 
                      # One is update, one is create, either way the operation is hadled through the same path
                      "withdraw": "VlEXsrENOWzsbglJZFLXZWqadeGcBcwl",
                      "reject": "ucE6pl2renvPrqEi49KDNS1SWq8NiDld" }
        self.validated_data ={
            "id": "6785568a242ecb29d4772fa4",
            "workspaceId": "65c249bfedeea53ae19d7dad",
            "policyId": "65dcb9cb19625023f282241d",
            "userId": "65bd6a6077682a20767a6c0b",
            "requesterUserId": "65dcdd57ea15ab53ab7b14db",
            "timeZone": "America/Edmonton",
            "timeOffPeriod": {
                "period": {
                    "start": "2025-01-15T19:30:00Z",
                    "end": "2025-01-15T23:30:00Z"
                },
                "halfDay": False,
                "halfDayPeriod": "NOT_DEFINED",
                "halfDayHours": None
            },
            "status": {
                "statusType": "APPROVED",
                "changedByUserId": "663e3575b2ff944858575793",
                "changedByUserName": "Don Fillmore",
                "changedForUserName": "Kendal Cruz",
                "changedAt": "2025-01-13T18:14:41.671710389Z",
                "note": None
            },
            "note": "Dr. Appointment",
            "createdAt": "2025-01-13T18:08:10.780128022Z",
            "excludeDays": [],
            "balanceDiff": 4,
            "negativeBalanceUsed": 0,
            "balanceValueAtRequest": 32,
            "recipients": []
        }
    
    @patch('Clockify.views.taskResult.delay')
    def testNewTimeoff(self, mockTaskResult: MagicMock):
        """Test valid new time off is saved correctly"""
        mockTaskResult.return_value = None
        
        response = async_to_sync(Clockify.views.TimeoffRequestsView.as_view())(buildRequest(self.url, self._secret['create'], self.validated_data))
        
        mockTaskResult.assert_called_once()
        self.assertEqual(response.status_code, 202)
        
    @patch('Clockify.views.taskResult.delay')
    def testUpdateTimeOff(self, mockTaskResult: MagicMock):
        """Test valid new time off is saved correctly"""
        mockTaskResult.return_value = None
        #ensure the record exists in database 
        view = Clockify.views.TimeoffRequestsView()
        self.assertTrue(view.processTimeOff( self.validated_data))

        response = async_to_sync(Clockify.views.TimeoffRequestsView.as_view())(buildRequest(self.url, self._secret['update'], self.validated_data))
        
        mockTaskResult.assert_called_once()
        self.assertEqual(response.status_code, 202)
        
    @patch('Clockify.views.taskResult.delay')
    def testRemoveTimeOff(self, mockTaskResult: MagicMock):
        """Test valid new time off is saved correctly"""
        mockTaskResult.return_value = None
        #ensure the record exists in database 
        view = Clockify.views.TimeoffRequestsView()
        self.assertTrue(view.processTimeOff( self.validated_data))
        
        response = async_to_sync(Clockify.views.TimeoffRequestsView.as_view())(buildRequest(self.url, self._secret['reject'], self.validated_data))
        self.assertEqual(Clockify.models.TimeOffRequests.objects.count(), 0)
        mockTaskResult.assert_called_once()
        self.assertEqual(response.status_code, 202)
        
