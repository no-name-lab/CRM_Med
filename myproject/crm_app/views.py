from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from django.utils.dateparse import parse_date
from .serializers import *
from doctor.models import Appointment, Patient, Doctor, DoctorSchedule, Department, CustomUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import  SearchFilter
from decimal import Decimal
from rest_framework_simplejwt.views import  TokenObtainPairView


class RegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        serializer =self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(serializer.data,  status=status.HTTP_201_CREATED)


class CustomLoginView(TokenObtainPairView):
    serializer_class =LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response({"detail": "Неверные учетные данные"}, status=status.HTTP_401_UNAUTHORIZED)

        user = serializer.validated_data
        return Response(serializer.data, status = status.HTTP_200_OK)


class CustomAdminLoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response({"detail": "Неверные учетные данные"}, status=status.HTTP_401_UNAUTHORIZED)

        user = serializer.validated_data.get('user')

        if not user.is_staff and not user.is_superuser:
            return Response({"detail": "Доступ разрешен только администраторам"},
                            status=status.HTTP_403_FORBIDDEN)

        return Response(serializer.data, status=status.HTTP_200_OK)


class LogoutView(generics.GenericAPIView):
    serializer_class = EmptySerializer
    def post(self, request, *args, **kwargs ):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)


#Записи на прием
class AppointmentListApiView(generics.ListAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentAdminSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['doctor', 'department', 'date']


#Добавление пациента
class PatientCreateApView(generics.CreateAPIView):
    serializer_class = AppointmentPatientSerializer


#ИНФО О ПАЦИЕНТЕ
class AppointmentDetailApiView(generics.RetrieveAPIView):
    queryset = Appointment.objects.all()
    serializer_class = InfoAppointmentSerializer


#История записей
class PatientAppointmentReportView(generics.RetrieveAPIView):
    serializer_class = PatientAppointmentsFullSerializer
    queryset = Patient.objects.all()

    def delete(self, request, *args, **kwargs):
        patient_id = self.kwargs.get('pk')
        appointment_ids = request.data.get('ids', [])

        if not isinstance(appointment_ids, list):
            return Response({"error": "Передайте список id приёмов в поле 'ids'."}, status=400)

        try:
            patient = Patient.objects.get(pk=patient_id)
        except Patient.DoesNotExist:
            return Response({"error": "Пациент не найден."}, status=404)

        deleted_count, _ = Appointment.objects.filter(id__in=appointment_ids, patient=patient).delete()

        return Response({"deleted": deleted_count}, status=200)


#История приемов
class PatientWaitingAppointmentsAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientWaitingAppointmentsFullSerializer


#Оплата
class PatientPaymentReportView(generics.RetrieveAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientPaymentReportSerializer


#Данные пациента
class InfoPatientApiView(generics.RetrieveAPIView):
    queryset = Patient.objects.all()
    serializer_class = InfoPatientSerializer


#Список врачей
class DoctorsApiView(generics.ListAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorsSerializer


#Добавление врача
class DoctorCreateApiView(generics.CreateAPIView):
    serializer_class = DoctorCreateSerializer


#Сохранение врача
class DoctorSaveApiView(generics.ListCreateAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSaveSerializer


#Подробный отчет
class DoctorAppointmentsApiView(generics.RetrieveAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorAppointmentsFullSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['user', 'department']
    search_fields = ['speciality']


#по врачам (процент врачам)
class DoctorDailyBonusListView(generics.ListAPIView):
    serializer_class = DoctorDailyBonusSerializer

    def get_queryset(self):
        queryset = Appointment.objects.select_related('doctor', 'doctor__user')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if start_date and end_date:
            queryset = queryset.filter(date__range=[start_date, end_date])
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        bonus_sum = Decimal('0')
        for obj in queryset:
            percent = Decimal(getattr(obj.doctor, 'bonus', 0)) / Decimal('100')
            price = Decimal(obj.price or 0)
            discount = Decimal(obj.discount or 0) / Decimal('100')
            discounted_price = price - (price * discount)
            bonus_sum += discounted_price * percent

        return Response({
            'results': serializer.data,
            'total_bonus_sum': round(bonus_sum, 2)
        })


#Сводный отчет
class ClinicSummaryReportView(generics.RetrieveAPIView):
    serializer_class = ClinicSummaryReportSerializer

    def get_object(self):
        start_date = parse_date(self.request.query_params.get('start_date'))
        end_date = parse_date(self.request.query_params.get('end_date'))

        # Получаем отфильтрованные приёмы по дате
        queryset = Appointment.objects.all()
        if start_date and end_date:
            queryset = queryset.filter(date__range=(start_date, end_date))
        elif start_date:
            queryset = queryset.filter(date__gte=start_date)
        elif end_date:
            queryset = queryset.filter(date__lte=end_date)

        # Создаём фиктивный объект с аннотированными методами
        report = Appointment()
        report.filtered_queryset = queryset  # временно прикрепляем к объекту
        return report


# Управление календарем
class DoctorScheduleApiView(generics.ListAPIView):
    queryset = DoctorSchedule.objects.all()
    serializer_class = DoctorScheduleSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['doctor']


#Прайс лист
class PriceListApiView(generics.ListAPIView):
    queryset = Department.objects.all()
    serializer_class = PriceListSerializer