import django.core.validators
import django.db.models.deletion
import phonenumber_field.modelfields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('phone_number', phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128, null=True, region='KG')),
                ('first_name', models.CharField(blank=True, max_length=60)),
                ('last_name', models.CharField(blank=True, max_length=60)),
                ('age', models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(140)])),
                ('profile_picture', models.ImageField(blank=True, null=True, upload_to='profile_pics/')),
                ('gender', models.CharField(choices=[('Male', 'male'), ('Female', 'female')], max_length=32)),
                ('role', models.CharField(choices=[('Admin', 'admin'), ('Reception', 'reception'), ('Doctor', 'doctor')], max_length=32)),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
            ],
        ),
        migrations.CreateModel(
            name='EmailLoginCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254)),
                ('code', models.CharField(max_length=6)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Doctor',
            fields=[
                ('userprofile_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('speciality', models.CharField(max_length=256)),
                ('medical_license', models.CharField(blank=True, max_length=256, null=True)),
                ('bonus', models.PositiveIntegerField(blank=True, default=0, null=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to='doctor_img/')),
                ('cabinet', models.SmallIntegerField()),
                ('job_title', models.CharField(blank=True, max_length=34, null=True)),
                ('department', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='departament_doctor', to='reception.department')),
            ],
            options={
                'verbose_name': 'Doctor',
            },
            bases=('reception.userprofile',),
        ),
        migrations.CreateModel(
            name='Reception',
            fields=[
                ('userprofile_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('desk_name', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name': 'Reception',
            },
            bases=('reception.userprofile',),
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('price', models.PositiveIntegerField(default=0)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='services', to='reception.department')),
            ],
        ),
        migrations.CreateModel(
            name='PriceList',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.PositiveIntegerField()),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='departament_price_list', to='reception.department')),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='price_service', to='reception.service')),
            ],
        ),
        migrations.CreateModel(
            name='Patient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=64)),
                ('date_birth', models.DateField()),
                ('gender', models.CharField(choices=[('male', 'Мужской'), ('female', 'Женский')], max_length=10)),
                ('phone_number', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region='KG')),
                ('status', models.CharField(choices=[('Живая очередь', 'Живая очередь'), ('Предзапись', 'Предзапись'), ('Отменено', 'Отменено')], default='Предзапись', max_length=20)),
                ('department', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='patient_depart', to='reception.department')),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='patient_profile', to=settings.AUTH_USER_MODEL)),
                ('service', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='reception.service')),
                ('doctor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='doctor_for_patientcreate', to='reception.doctor')),
                ('reception', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reception_patient', to='reception.reception')),
            ],
        ),
        migrations.CreateModel(
            name='CustomerRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.PositiveIntegerField(blank=True, default=0, null=True)),
                ('change', models.PositiveIntegerField(blank=True, null=True)),
                ('payment_type', models.CharField(blank=True, choices=[('cash', 'Наличные'), ('card', 'Карта')], default='cash', max_length=10, null=True)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('Живая очередь', 'Живая очередь'), ('Предзапись', 'Предзапись'), ('Отменено', 'Отменено')], default='Живая очередь', max_length=20)),
                ('records', models.CharField(choices=[('был в приеме', 'был в приеме'), ('в ожидании', 'в ожидании'), ('отменен', 'отменен')], default='был в приеме', max_length=16)),
                ('phone_number', phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128, null=True, region='KG')),
                ('time', models.TimeField(blank=True, null=True)),
                ('discount', models.PositiveIntegerField(default=0)),
                ('start_at', models.TimeField(blank=True, default='10:00', null=True)),
                ('end_at', models.TimeField(blank=True, default='10:00', null=True)),
                ('department', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cust_dep', to='reception.department')),
                ('patient', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='customer_record', to='reception.patient')),
                ('service', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='reception.service')),
                ('doctor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='doctor_customer', to='reception.doctor')),
                ('reception', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reception_customer', to='reception.reception')),
            ],
        ),
        migrations.CreateModel(
            name='HistoryRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True)),
                ('record', models.CharField(choices=[('был в приеме', 'был в приеме'), ('в ожидании', 'в ожидании'), ('отменен', 'отменен')], default='в ожидании', max_length=16)),
                ('description', models.TextField()),
                ('departament', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='departament_history', to='reception.department')),
                ('payment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_history', to='reception.customerrecord')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='patient_history', to='reception.patient')),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='service_history', to='reception.service')),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='doctor_history', to='reception.doctor')),
                ('reception', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reception_history', to='reception.reception')),
            ],
        ),
    ]
