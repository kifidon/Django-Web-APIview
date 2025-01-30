# Generated by Django 5.0.4 on 2024-12-12 05:07

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Calendar',
            fields=[
                ('date', models.DateField(primary_key=True, serialize=False)),
                ('dayofweek', models.IntegerField(blank=True, db_column='dayOfWeek', null=True)),
                ('month', models.IntegerField(blank=True, null=True)),
                ('year', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'db_table': 'Calendar',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('email', models.CharField(blank=True, max_length=50, null=True)),
                ('address', models.CharField(blank=True, max_length=100, null=True)),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'db_table': 'Client',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Employeeuser',
            fields=[
                ('id', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('email', models.CharField(blank=True, max_length=255, null=True)),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('status', models.CharField(blank=True, max_length=50, null=True)),
                ('role', models.CharField(blank=True, db_column='role', max_length=50, null=True)),
                ('manager', models.CharField(blank=True, db_column='manager', max_length=50, null=True)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('hourly', models.IntegerField(blank=True, db_column='hourly', default=0, null=True)),
                ('Truck', models.IntegerField(db_column='hasTruck', default=0, null=True)),
                ('truckDetails', models.CharField(blank=True, db_column='truckDetails', max_length=50, null=True)),
            ],
            options={
                'db_table': 'EmployeeUser',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Holidays',
            fields=[
                ('id', models.CharField(db_column='holidayID', max_length=50, primary_key=True, serialize=False)),
                ('date', models.DateField(blank=True, null=True)),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'Holidays',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Workspace',
            fields=[
                ('id', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, max_length=50, null=True)),
            ],
            options={
                'db_table': 'Workspace',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='FilesForExpense',
            fields=[
                ('expenseId', models.CharField(db_column='expenseId', max_length=64, primary_key=True, serialize=False)),
                ('workspaceId', models.CharField(db_column='workspaceId', max_length=50)),
                ('binaryData', models.TextField(db_column='binaryData')),
            ],
            options={
                'db_table': 'FilesForExpense',
                'managed': True,
                'unique_together': {('expenseId', 'workspaceId')},
            },
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True, null=True)),
                ('title', models.TextField(blank=True, null=True)),
                ('code', models.CharField(blank=True, max_length=50, null=True)),
                ('clientId', models.ForeignKey(db_column='client_id', on_delete=django.db.models.deletion.DO_NOTHING, to='Clockify.client')),
                ('workspaceId', models.ForeignKey(db_column='workspace_id', on_delete=django.db.models.deletion.DO_NOTHING, to='Clockify.workspace')),
            ],
            options={
                'db_table': 'Project',
                'managed': True,
                'unique_together': {('id', 'workspaceId')},
            },
        ),
        migrations.CreateModel(
            name='Timesheet',
            fields=[
                ('id', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('start_time', models.DateField(blank=True, null=True)),
                ('end_time', models.DateField(blank=True, null=True)),
                ('status', models.CharField(blank=True, max_length=50, null=True)),
                ('emp', models.ForeignKey(db_column='emp_id', on_delete=django.db.models.deletion.DO_NOTHING, to='Clockify.employeeuser')),
                ('workspace', models.ForeignKey(db_column='workspace_id', on_delete=django.db.models.deletion.DO_NOTHING, to='Clockify.workspace')),
            ],
            options={
                'db_table': 'TimeSheet',
                'managed': True,
                'unique_together': {('emp', 'id', 'workspace'), ('id', 'workspace')},
            },
        ),
        migrations.CreateModel(
            name='Entry',
            fields=[
                ('id', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('duration', models.FloatField(blank=True, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('task', models.CharField(blank=True, max_length=200, null=True)),
                ('billable', models.BooleanField(blank=True, null=True)),
                ('hourlyRate', models.DecimalField(blank=True, db_column='rate', decimal_places=2, max_digits=10, null=True)),
                ('start', models.DateTimeField(blank=True, db_column='start_time', null=True)),
                ('end', models.DateTimeField(blank=True, db_column='end_time', null=True)),
                ('project', models.ForeignKey(blank=True, db_column='project_id', null=True, on_delete=django.db.models.deletion.CASCADE, to='Clockify.project')),
                ('timesheetId', models.ForeignKey(blank=True, db_column='time_sheet_id', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='Clockify.timesheet')),
                ('workspaceId', models.ForeignKey(db_column='workspace_id', on_delete=django.db.models.deletion.DO_NOTHING, to='Clockify.workspace')),
            ],
            options={
                'db_table': 'Entry',
                'managed': True,
                'unique_together': {('id', 'workspaceId')},
            },
        ),
        migrations.AddField(
            model_name='client',
            name='workspace',
            field=models.ForeignKey(db_column='workspace_id', on_delete=django.db.models.deletion.DO_NOTHING, to='Clockify.workspace'),
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('hasUnitPrice', models.BooleanField(default=False, max_length=1)),
                ('unit', models.CharField(blank=True, max_length=50, null=True)),
                ('archived', models.BooleanField(default=False, max_length=1)),
                ('priceInCents', models.IntegerField(blank=True, default=0, null=True)),
                ('workspaceId', models.ForeignKey(db_column='workspaceId', on_delete=django.db.models.deletion.DO_NOTHING, to='Clockify.workspace')),
            ],
            options={
                'db_table': 'ExpenseCategory',
                'managed': True,
                'unique_together': {('id', 'workspaceId')},
            },
        ),
        migrations.CreateModel(
            name='TimeOffRequests',
            fields=[
                ('id', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('policyId', models.CharField(db_column='pID', max_length=50)),
                ('start', models.DateTimeField(db_column='startDate')),
                ('end', models.DateTimeField(db_column='end_date')),
                ('duration', models.FloatField(default=0)),
                ('balanceDiff', models.FloatField(db_column='paidTimeOff', default=0)),
                ('status', models.CharField(max_length=50)),
                ('userId', models.ForeignKey(db_column='eID', on_delete=django.db.models.deletion.DO_NOTHING, to='Clockify.employeeuser')),
                ('workspaceId', models.ForeignKey(db_column='workspace_id', on_delete=django.db.models.deletion.DO_NOTHING, to='Clockify.workspace')),
            ],
            options={
                'db_table': 'TimeOffRequests',
                'managed': True,
                'unique_together': {('id', 'workspaceId')},
            },
        ),
        migrations.CreateModel(
            name='Tagsfor',
            fields=[
                ('recordId', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('id', models.CharField(max_length=50)),
                ('name', models.CharField(blank=True, max_length=50, null=True)),
                ('entryid', models.ForeignKey(db_column='entryID', on_delete=django.db.models.deletion.DO_NOTHING, to='Clockify.entry')),
                ('workspaceId', models.ForeignKey(db_column='workspace_id', on_delete=django.db.models.deletion.DO_NOTHING, to='Clockify.workspace')),
            ],
            options={
                'db_table': 'TagsFor',
                'managed': True,
                'unique_together': {('id', 'entryid', 'workspaceId')},
            },
        ),
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.CharField(max_length=64, primary_key=True, serialize=False)),
                ('date', models.DateField()),
                ('notes', models.TextField(blank=True, null=True)),
                ('quantity', models.FloatField(blank=True, null=True)),
                ('subTotal', models.FloatField(blank=True, null=True)),
                ('taxes', models.FloatField(blank=True, null=True)),
                ('status', models.CharField(blank=True, default='PENDING', max_length=50, null=True)),
                ('categoryId', models.ForeignKey(db_column='categoryId', on_delete=django.db.models.deletion.DO_NOTHING, to='Clockify.category')),
                ('userId', models.ForeignKey(db_column='userId', on_delete=django.db.models.deletion.DO_NOTHING, to='Clockify.employeeuser')),
                ('projectId', models.ForeignKey(db_column='projectId', on_delete=django.db.models.deletion.DO_NOTHING, to='Clockify.project')),
                ('workspaceId', models.ForeignKey(db_column='workspaceId', on_delete=django.db.models.deletion.DO_NOTHING, to='Clockify.workspace')),
            ],
            options={
                'db_table': 'Expense',
                'managed': True,
                'unique_together': {('id', 'workspaceId')},
            },
        ),
        migrations.AlterUniqueTogether(
            name='client',
            unique_together={('id', 'workspace')},
        ),
    ]
