from email import policy
from tracemalloc import start
from venv import logger
from celery import Task
from rest_framework import serializers
from HillPlainAPI.Loggers import setup_background_logger
from .models import *
from rest_framework.exceptions import ValidationError
from Utilities.views import count_working_daysV2, toMST, timeDuration
from json import dumps
from datetime import date, datetime, timedelta
from dateutil import parser


class EmployeeUserSerializer(serializers.ModelSerializer):
    '''
    Serialized to the EmployeeUser Model fields. 
    Input Data is of the form: 
        {
            "id": "65dcdd57ea15ab53ab7b14db",
            "email": "kendal.cruz@hillplain.com",
            "name": "Kendal Cruz",
            "profilePicture": "https://img.clockify.me/no-user-image.png",
            "settings": {
                "weekStart": "SUNDAY",
                "timeZone": "America/Edmonton",
                "timeFormat": "HOUR12",
                "dateFormat": "MM/DD/YYYY",
                "sendNewsletter": false,
                "weeklyUpdates": false,
                "longRunning": false,
                "scheduledReports": true,
                "approval": true,
                "pto": true,
                "alerts": true,
                "reminders": true,
                "onboarding": true,
                "timeTrackingManual": false,
                "summaryReportSettings": {
                    "group": "Project",
                    "subgroup": "Time Entry"
                },
                "isCompactViewOn": false,
                "dashboardSelection": "ME",
                "dashboardViewType": "PROJECT",
                "dashboardPinToTop": false,
                "projectListCollapse": 50,
                "collapseAllProjectLists": false,
                "groupSimilarEntriesDisabled": false,
                "myStartOfDay": "08:30",
                "darkTheme": true,
                "projectPickerSpecialFilter": false,
                "lang": "EN",
                "multiFactorEnabled": false,
                "scheduling": true,
                "showOnlyWorkingDays": false,
                "theme": "DARK"
            },
            "userCustomFields": [
                {
                    "customFieldId": "664d0d0a6a8fa06c786a886e",
                    "value": "HSEA",
                    "name": "Role",
                    "type": "DROPDOWN_SINGLE"
                },
                {
                    "customFieldId": "664d0d56a17be2283ae908ec",
                    "value": "2024-01-22",
                    "name": "Start Date",
                    "type": "TXT"
                }
            ]
        } 
    '''
    status = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()  # validate this later 
    end_date = serializers.SerializerMethodField()  # validate this later 
    Truck = serializers.SerializerMethodField()
    hourly = serializers.SerializerMethodField()
    manager = serializers.SerializerMethodField()
    truckDetails = serializers.SerializerMethodField()

    def get_status(self, obj):
        status = obj['status']
        return status

    def get_hasTruck(self, obj):
        logger = setup_background_logger()
        field = dict()
        for custom in obj['userCustomFields']:
            field[custom['name']] = custom['value']
        try:
            if field['Truck']:
                return 1
            else:
                return 0
        except Exception as e:
            logger.debug(type(e))

            return 0

    def get_role(self, obj):
        field = dict()
        for custom in obj['userCustomFields']:
            field[custom['name']] = custom['value']
        try:
            return field['Role']
        except Exception:
            return 'No Role Specified'

    def get_start_date(self, obj):
        field = dict()
        for custom in obj['userCustomFields']:
            field[custom['name']] = custom['value']
        try:
            return field['Start Date']
        except Exception:
            return date.today().strftime('%Y-%m-%d')

    def get_end_date(self, obj):
        field = dict()
        for custom in obj['userCustomFields']:
            field[custom['name']] = custom['value']
        try:
            return field['End Date']
        except Exception:
            return date.today().strftime('%Y-%m-%d')

    def get_hourly(self, obj):
        logger = setup_background_logger()
        field = dict()
        for custom in obj['userCustomFields']:
            field[custom['name']] = custom['value']
        try:
            return field['Rate Type']
        except Exception as e:
            logger.error(f'({str(e)})')
            return 5

    def get_manager(self, obj):
        field = dict()
        for custom in obj['userCustomFields']:
            field[custom['name']] = custom['value']
        try:
            return field['Reporting Manager']
        except Exception:
            return 'Missing Manager Information'

    def get_truckDetails(self, obj):
        field = dict()
        for custom in obj['userCustomFields']:
            field[custom['name']] = custom['value']
        try:
            return field['Truck Details']
        except Exception:
            return 'Missing Details'

    def create(self, validated_data):
        logger = setup_background_logger()
        try:
            logger.debug(self.initial_data)
            validated_data['status'] = self.get_status(self.initial_data)
            validated_data['Truck'] = self.get_hasTruck(self.initial_data)
            validated_data['role'] = self.get_role(self.initial_data)
            validated_data['start_date'] = self.get_start_date(self.initial_data)
            validated_data['end_date'] = self.get_end_date(self.initial_data)
            validated_data['hourly'] = self.get_hourly(self.initial_data)
            validated_data['manager'] = self.get_manager(self.initial_data)
            validated_data['truckDetails'] = self.get_truckDetails(self.initial_data)
            logger.info(dumps(validated_data, indent=4))
            return super().create(validated_data=validated_data)
        except Exception as e:
            logger.error(f'Problem inserting User Data {e.__traceback__.tb_lineno}: ({str(e)})')

    def update(self, instance, validated_data):
        logger = setup_background_logger()
        logger.debug(self.initial_data)
        try:
            validated_data['status'] = self.get_status(self.initial_data)
            validated_data['role'] = self.get_role(self.initial_data)
            validated_data['start_date'] = self.get_start_date(self.initial_data)
            validated_data['end_date'] = self.get_end_date(self.initial_data)
            validated_data['Truck'] = self.get_hasTruck(self.initial_data)
            validated_data['hourly'] = self.get_hourly(self.initial_data)
            validated_data['manager'] = self.get_manager(self.initial_data)
            validated_data['truckDetails'] = self.get_truckDetails(self.initial_data)
            logger.debug(dumps(validated_data, indent=4))
            updated = super().update(instance=instance, validated_data=validated_data)
            updated.save(force_update=True)
            return updated
        except Exception as e:
            logger.error(f'Problem Updating User Data {e.__traceback__.tb_lineno}: ({str(e)})')
            raise e

    class Meta:
        model = Employeeuser
        fields = '__all__'


class TimesheetSerializer(serializers.Serializer):
    '''
    Input is of the form: 
    {
        "id": "664d12ce831d3f5360a7c43c",
        "workspaceId": "65c249bfedeea53ae19d7dad",
        "dateRange": {
            "start": "2024-05-12T06:00:00Z",
            "end": "2024-05-19T05:59:59Z"
        },
        "owner": {
            "userId": "65dcdd57ea15ab53ab7b14d0",
            "userName": "Mohamad Potts",
            "timeZone": "America/Denver",
            "startOfWeek": "SUNDAY"
        },
        "status": {
            "state": "APPROVED",
            "updatedBy": "65dcdd57ea15ab53ab7b14d0",
            "updatedByUserName": "Mohamad Potts",
            "updatedAt": "2024-05-21T21:31:58Z",
            "note": ""
        },
        "creator": {
            "userId": "65dcdd57ea15ab53ab7b14d0",
            "userName": "Mohamad Potts",
            "userEmail": "mohamad.potts@hillplain.com"
        }
    }
    '''
    id = serializers.CharField()
    owner = serializers.DictField()
    workspaceId = serializers.CharField()
    dateRange = serializers.DictField()
    status = serializers.DictField()

    def create(self, validated_data):

        timesheet = Timesheet.objects.create(
            id=validated_data['id'],
            workspace=Workspace.objects.get(id=validated_data['workspaceId']),
            emp=Employeeuser.objects.get(id=validated_data.get('owner').get('userId')),
            start_time=datetime.strptime(validated_data.get('dateRange').get('start'), '%Y-%m-%dT%H:%M:%SZ').date(),
            end_time=datetime.strptime(validated_data.get('dateRange').get('end'),
                                       '%Y-%m-%dT%H:%M:%SZ').date() - timedelta(days=1),
            status=validated_data.get('status').get('state')
        )
        return timesheet

    def update(self, instance: Timesheet, validated_data):
        try:
            instance.id = instance.id
            # print("\n", validated_data, '\n', vars(instance) )
            instance.workspace = Workspace.objects.get(id=validated_data['workspaceId']) or instance.workspace
            instance.emp = Employeeuser.objects.get(id=validated_data.get('owner').get('userId')) or instance.emp
            instance.start_time = datetime.strptime(validated_data.get('dateRange').get('start'),
                                                    '%Y-%m-%dT%H:%M:%SZ').date() or instance.start_time
            instance.end_time = datetime.strptime(validated_data.get('dateRange').get('end'),
                                                  '%Y-%m-%dT%H:%M:%SZ').date() - timedelta(days=1) or instance.end_time
            instance.status = validated_data.get('status').get('state') or instance.status
            instance.save(force_update=True)
        except Exception as e:
            print(e.__traceback__.tb_lineno)
            raise ValidationError(f"Cannot save Timesheet: {e}")
        return instance


class EntrySerializer(serializers.ModelSerializer):
    '''
    Input is of the form: 
    {
        "approvalRequestId": "5e4117fe8c625f38930d57b7",
        "billable": true,
        "costRate": {},
        "customFieldValues": [],
        "description": "This is a sample time entry description.",
        "hourlyRate": {},
        "id": "5b715448b0798751107918ab",
        "isLocked": true,
        "project": {},
        "tags": [],
        "task": {},
        "timeInterval": {},
        "type": "REGULAR"
    }
    '''
    id = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    billable = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    timesheetId = serializers.SerializerMethodField()
    project = serializers.SerializerMethodField()
    hourlyRate = serializers.SerializerMethodField()
    start = serializers.SerializerMethodField()
    end = serializers.SerializerMethodField()
    task = serializers.SerializerMethodField()
    workspaceId = serializers.SerializerMethodField()
    

    def is_valid(self, raise_exception=True):
        try:
            super().is_valid()
            self.validated_data['id'] = self.initial_data.get('id')
            self.validated_data['description'] = self.initial_data.get('description')
            self.validated_data['billable'] = self.initial_data.get('billable')
            self.validated_data['duration'] = timeDuration(self.initial_data['timeInterval']['duration'])
            self.validated_data['timesheetId'] = self.validateTimesheet()
            self.validated_data['project'] = self.validateProject()
            self.validated_data['hourlyRate'] = self.validateRate()
            start, end = self.validateTime()
            self.validated_data['start'] = start
            self.validated_data['end'] = end
            self.validated_data['task'] = self.validateTask()
            self.validated_data['workspaceId'] = Workspace.objects.get(id=self.initial_data.get('workspaceId')) 
            return True
        except ValidationError as e:
            logger = setup_background_logger()
            logger.error(f'Cannot Save Entry: {e}')
            raise e
    
    def validateTimesheet(self):
        try:
            timesheet = Timesheet.objects.get(id=self.initial_data['timesheetId'])
        except Exception as e:
            timesheet = None
        return timesheet
    
    def validateProject(self,):
        try:
            project = Project.objects.get(id=self.initial_data.get('project').get('id'))
            return project
        except Exception as e:
            project = Project.objects.get(id = '65c262c0edeea53ae1a27b84')
            logger.warning(f'Project {self.initial_data.get("project").get("id")} does not exist in database. Review entry {self.initial_data.get('id')}')
            # raise ValidationError(f'Project Not Found: {self.initial_data.get("project").get("id")}')
    def validateRate(self):
        if self.initial_data['billable'] == True:
            if self.initial_data.get('hourlyRate') is None:
                Rate = 0
            else:
                Rate = self.initial_data.get('hourlyRate').get('amount')
        else:
            Rate = 0
        return Rate
    def validateTime(self):
        if isinstance(self.initial_data.get('timeInterval').get('start'), str):
            start_time = toMST(datetime.strptime(self.initial_data.get('timeInterval').get('start'), '%Y-%m-%dT%H:%M:%SZ'), True)
        if isinstance(self.initial_data.get('timeInterval').get('end'), str):
            end_time   = toMST(datetime.strptime(self.initial_data.get('timeInterval').get('end'), '%Y-%m-%dT%H:%M:%SZ'), True)
        else: raise ValidationError('Invalid Time Format')
        return start_time, end_time
    def validateTask(self):
        if self.initial_data.get('task') is not None:
            TASK = self.initial_data.get('task').get('name') or None
        else: TASK = None
        return TASK
    
    def create(self, validated_data):
        return super().create(validated_data=validated_data)

    def update(self, instance: Entry, validated_data):
        updated_instance = super().update(instance=instance, validated_data=validated_data)
        updated_instance.save(force_update=True)
        return updated_instance
    
    class Meta:
        model = Entry
        fields = '__all__'

class TagsForSerializer(serializers.ModelSerializer):
    '''
    Input is of the form: 
    {
        "entryid": "adasdfadf ada"
        "archived": true,
        "id": "64c777ddd3fcab07cfbb210c",
        "name": "Sprint1",
        "workspaceId": "64a687e29ae1f428e7ebe303"
    }
    '''

    class Meta:
        model = Tagsfor
        fields = "__all__"

    # def create(self,validated_data:dict):
    #     try: 
    #         logger = setup_background_logger('DEBUG')
    #         logger.info('Create Tag Called')
    #         entryInstnace = Entry.objects.get(
    #                             id=self.get_entryid(),
    #                             workspaceId=validated_data.get('workspaceId')
    #                         )
    #         tag = Tagsfor.objects.create(
    #             id = validated_data.get('id'),
    #             entryid = entryInstnace,
    #             workspaceId = Workspace.objects.get(id= validated_data.get('workspaceId')),
    #             name = validated_data.get('name')
    #         )
    #         return tag
    #     except Exception as e:
    #         logger.error(f'Error Caught ({e.__traceback__.tb_lineno}): {str(e)}')
    #         raise e 

    def update(self, instance, validated_data):
        logger = setup_background_logger('DEBUG')
        logger.info('Update Tag Called')
        try:
            instance.name = validated_data.get('name', instance.name)

            # Ensuring that primary key fields are not changed
            # instance.id = instance.id
            # instance.workspace = instance.workspace
            # instance.entryid = instance.entryid

            # Save the instance
            logger.warning(f"\tUpdate on Tags For Entry is a Forbidden Opperation. Returning...")
            return instance
        except Exception as e:
            logger.warning(f'UnknownError: {dumps(str(e), indent=4)}')
            raise e


class CategorySerializer(serializers.ModelSerializer):
    '''
    Input is of the form: 
        {
            "archived": true,
            "hasUnitPrice": true,
            "id": "89a687e29ae1f428e7ebe303",
            "name": "Procurement",
            "priceInCents": 1000,
            "unit": "piece",
            "workspaceId": "64a687e29ae1f428e7ebe303"
        }
    '''

    class Meta:
        model = Category
        fields = ['id', 'hasUnitPrice', 'archived', 'name', 'priceInCents', 'unit', 'workspaceId']


class ExpenseSerializer(serializers.ModelSerializer):
    '''
    Input is of the form: 
        {
            "id": "66463e0a58c2983f17f453ae",
            "workspaceId": "65c249bfedeea53ae19d7dad",
            "userId": "661d41f8680b5d3887e576e8",
            "date": "2024-05-16T00:00:00Z",
            "projectId": "65c5185e824ced2beacffa9a",
            "categoryId": "65c2522effbbb676c5e010b4",
            "notes": "Paid Elder for smudge ceremony",
            "quantity": 1,
            "billable": true,
            "fileId": "",
            "total": 10000
        }
    '''
    date = serializers.DateField(input_formats=['%m/%d/%Y'])

    class Meta:
        model = Expense
        fields = "__all__"


class TimeOffSerializer(serializers.ModelSerializer):
    '''
    Input is of the form: 
        {
            "workspaceId": "65c249bfedeea53ae19d7dad",
            "policyId": "65fc91ca17e548286f7bc026",
            "userId": "65bd6a6077682a20767a6c0b",
            "timeZone": "America/Edmonton",
            "timeOffPeriod": {
                "period": {
                    "start": "2024-05-14T14:00:00Z",
                    "end": "2024-05-14T22:00:00Z"
                },
                "halfDay": false,
                "halfDayPeriod": "NOT_DEFINED"
            },
            "note": null,
            "status": {
                "statusType": "PENDING",
                "changedByUserId": null,
                "changedByUserName": "Timmy Ifidon",
                "changedAt": null,
                "note": null
            },
            "balanceDiff": 8,
            "createdAt": "2024-05-21T18:15:52.889302519Z",
            "requesterUserId": "65bd6a6077682a20767a6c0b",
            "excludeDays": [],
            "negativeBalanceUsed": 0,
            "balanceValueAtRequest": 15,
            "id": "664ce4d8c8a2333cfdc245cc"
        }
    '''
    id = serializers.SerializerMethodField()
    userId = serializers.SerializerMethodField()
    policyId = serializers.SerializerMethodField()
    start  = serializers.SerializerMethodField()
    end = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    balanceDiff = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    workspaceId = serializers.SerializerMethodField()
    createdAt = serializers.SerializerMethodField()

    def is_valid(self, raise_exception=True):
        super().is_valid()
        try:
            start = toMST(self.initial_data.get('timeOffPeriod').get('period').get('start'), True)
            end = toMST(self.initial_data.get('timeOffPeriod').get('period').get('end'), True)
            createdAt = toMST(self.initial_data.get('createdAt'), False)
        except Exception as e:
            raise ValidationError(f"Invalid TimeOffPeriod: {e}")
        try:
            status = self.initial_data.get('status').get('statusType')
        except Exception as e:
            raise ValidationError(f"Invalid Status: {e}")
        try:
            duration = count_working_daysV2(start, end, self.initial_data.get('excludeDays'))
        except Exception as e:
            raise ValidationError(f"Invalid Duration: {e}")
        self.validated_data['start'] = start
        self.validated_data['end'] = end
        self.validated_data['status'] = status
        self.validated_data['duration'] = duration
        self.validated_data['createdAt'] = createdAt
        # handle FK objects 
        try:
            self.validated_data['userId'] = Employeeuser.objects.get(id=self.initial_data['userId'])
            self.validated_data['workspaceId'] = Workspace.objects.get(id = self.initial_data['workspaceId'])
            self.validated_data['policyId'] = self.initial_data.get('policyId')
        except Exception as e:
            raise ValidationError(f"Invalid FK Objects: {e}")
        
        self.validated_data['balanceDiff'] = self.initial_data.get('balanceDiff')
        self.validated_data['id'] = self.initial_data.get('id')
        logger = setup_background_logger()
        logger.debug(self.validated_data)
        return True

    def create(self, validated_data):
        return super().create(validated_data=validated_data)

    def update(self, instance, validated_data):
        updated_instance = super().update(instance=instance, validated_data=validated_data)
        updated_instance.save(force_update=True)
        return updated_instance

    class Meta:
        model = TimeOffRequests
        fields = '__all__'


class FileExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = FilesForExpense
        fields = "__all__"


class ProjectSerializer(serializers.ModelSerializer):
    '''
        {
        "id": "66b3acf08becbd615f4e40dc",
        "name": "LIL-003 - Lil'wat Business Group Office & Shop",
        "hourlyRate": {
            "amount": 0
        },
        "costRate": null,
        "clientId": "65e8b35c5590595c3ffd1e65",
        "workspaceId": "65c249bfedeea53ae19d7dad",
        "billable": true,
        "memberships": [
            {
                "userId": "664ce0a17abd9f73f7926cb6",
                "hourlyRate": null,
                "costRate": null,
                "targetId": "66b3acf08becbd615f4e40dc",
                "membershipType": "PROJECT",
                "membershipStatus": "ACTIVE"
            }
        ],
        "color": "#FF5722",
        "estimate": {
            "estimate": "PT0S",
            "type": "AUTO"
        },
        "archived": false,
        "duration": "PT0S",
        "clientName": "LIL",
        "note": "",
        "timeEstimate": {
            "estimate": "PT0S",
            "type": "AUTO",
            "resetOption": null,
            "active": false,
            "includeNonBillable": true
        },
        "budgetEstimate": null,
        "estimateReset": null,
        "currency": null,
        "template": false,
        "public": true,
        "tasks": [],
        "client": {
            "name": "LIL",
            "email": null,
            "address": "",
            "workspaceId": "65c249bfedeea53ae19d7dad",
            "archived": false,
            "note": "",
            "currencyId": {
                "timestamp": 1707858011,
                "counter": 1777596,
                "machineIdentifier": 2048178,
                "processIdentifier": 28965,
                "timeSecond": 1707858011,
                "time": 1707858011000,
                "date": 1707858011000
            },
            "id": "65e8b35c5590595c3ffd1e65"
        }
    }
    '''
    title = serializers.SerializerMethodField(required=False)
    code = serializers.SerializerMethodField(required=False)

    def get_code(self, obj: str):
        logger = setup_background_logger()
        try:
            code = obj.split(' - ')
            if len(code) != 2:
                raise ValueError
            return str(code[0])
        except ValueError as v:
            logger.warning('Project must have format XXX-XXX - Project Name ')
            return 'INVALID NAME FORMAT'

    def get_title(self, obj: str):
        logger = setup_background_logger()
        try:
            title = obj.split(' - ')
            if len(title) != 2:
                raise (ValueError)
            return str(title[1])
        except ValueError as v:
            logger.warning('Project must have format XXX-XXX - Project Name ')
            return 'INVALID NAME FORMAT'

    class Meta:
        model = Project
        fields = '__all__'

    def create(self, validated_data):
        obj = validated_data.get('name', '')
        validated_data['title'] = self.get_title(obj)
        validated_data['code'] = self.get_code(obj)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        obj = validated_data.get('name', '')
        validated_data['title'] = self.get_title(obj)
        validated_data['code'] = self.get_code(obj)
        updated = super().update(instance=instance, validated_data=validated_data)
        updated.save(force_update=True)
        return updated
