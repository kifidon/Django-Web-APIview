from django.test import TestCase
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
import LemApplication
from asgiref.sync import async_to_sync
from django.core.handlers.asgi import ASGIRequest
from Clockify.tests import buildRequest
import LemApplication.views


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


class LemSheetTestsCaases(TestCase):
    def setUp(self):
        self.validData = {
            "clientId": "65c25ae977682a2076d96d49",
            "lem_sheet_date": "2025-01-17",
            "projectId": "65c262c0edeea53ae1a27b84",
            "projectManagerId": "65bd6a6077682a20767a6c0b",
            "workspaceId": "65c249bfedeea53ae19d7dad",
            "description": "----",
            "notes": "----",
            "clientRep": "tIMMY IFIDON"
        }
        self.url = 'http://4.149.229.109:8000/HpClockifyApi/lemSheet'

    def testPostonLemSheet(self):
        request = buildRequest(self.url, '', self.validData)
        response = async_to_sync(LemApplication.views.lemSheet)(request)

        self.assertEqual(response.status_code, 202)