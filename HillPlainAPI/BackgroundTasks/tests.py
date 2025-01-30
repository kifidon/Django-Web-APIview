from django.http import JsonResponse
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch, AsyncMock, MagicMock
import BackgroundTasks
import BackgroundTasks.tasks
import BackgroundTasks.views

# Create your tests here.
class BackgroundTasksTest(TestCase): 
    def setUp(self):
        self.url = "http://localhost:8000/quickBackup"
        return super().setUp()
    
    @patch('BackgroundTasks.views.mainBackup')
    @patch('BackgroundTasks.views.taskResult.delay')
    def testClientbackup(self, mockTaskResult: MagicMock, mockMainBackup: MagicMock):
        mockTaskResult.return_value = None
        mockMainBackup.return_value = None
        response = self.client.get(self.url)
        mockTaskResult.assert_called_once()
        mockMainBackup.assert_called_once()
        self.assertEqual(response.status_code, 200)
        
    @patch('BackgroundTasks.tasks.BackGroundTaskResult.objects.create')    
    def testTaskResult(self, mockCreate: MagicMock):
        mockCreate.return_value = None
        response = JsonResponse({'status': 'success', 'message': 'Backup job submitted', 'data': 'results'})
        BackgroundTasks.tasks.taskResult(response.content, {}, 'caller')
        mockCreate.assert_called_once()

    def testClientOffBackup(self):
        '''Test ClientOffEvent: Sync function'''
        BackgroundTasks.tasks.TimeOffEvent()
        self.assertTrue(True)
        
    def testTimeOffBackup(self):
        '''Test TimeOffEvent: Async function'''
        BackgroundTasks.tasks.TimeOffEvent()
        self.assertTrue(True)