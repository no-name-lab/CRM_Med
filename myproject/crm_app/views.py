from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.views import  APIView
from reception.serializers import SummaryReportSerializer, DoctorReportSerializers
from .serializers import *
from reception.models import UserProfile, Patient, Doctor, Department, Service, CustomerRecord, HistoryRecord
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import  SearchFilter
from decimal import Decimal
from rest_framework_simplejwt.views import  TokenObtainPairView


class RegisterView(generics.CreateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "user": {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "role": user.role
            }
        }, status=status.HTTP_201_CREATED)


class CustomLoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response({"detail": "Неверные учетные данные"}, status=status.HTTP_401_UNAUTHORIZED)

        user = serializer.validated_data  # ✅ исправлено здесь

        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomAdminLoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response({"detail": "Неверные учетные данные"}, status=status.HTTP_401_UNAUTHORIZED)

        user = serializer.validated_data

        if not user.is_staff and not user.is_superuser:
            return Response({"detail": "Доступ разрешен только администраторам"},
                            status=status.HTTP_403_FORBIDDEN)

        return Response(serializer.data, status=status.HTTP_200_OK)


class LogoutView(generics.GenericAPIView):
    serializer_class = LogoutSerializer

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "Refresh токен отсутствует."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Вы вышли из системы."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"detail": "Ошибка обработки токена."}, status=status.HTTP_400_BAD_REQUEST)


#Записи на прием
class RecordsListApiView(generics.ListAPIView):
    queryset = CustomerRecord.objects.all()
    serializer_class = AppointmentAdminSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['doctor', 'department', 'created_date']
    search_fields = ['patient']


#Добавление пациента
class PatientCreateApView(generics.CreateAPIView):
    serializer_class = AppointmentPatientSerializer


#ИНФО О ПАЦИЕНТЕ
class RecordsDetailApiView(generics.RetrieveAPIView):
    queryset = CustomerRecord.objects.all()
    serializer_class = InfoAppointmentSerializer


#История записей
class PatientAppointmentReportView(generics.RetrieveAPIView):
    serializer_class = AppointmentHistorySerializer
    queryset = CustomerRecord.objects.all()

    def delete(self, request, *args, **kwargs):
        patient_id = self.kwargs.get('pk')
        appointment_ids = request.data.get('ids', [])

        if not isinstance(appointment_ids, list):
            return Response({"error": "Передайте список id приёмов в поле 'ids'."}, status=400)

        try:
            patient = Patient.objects.get(pk=patient_id)
        except Patient.DoesNotExist:
            return Response({"error": "Пациент не найден."}, status=404)

        deleted_count, _ = CustomerRecord.objects.filter(id__in=appointment_ids, patient=patient).delete()

        return Response({"deleted": deleted_count}, status=200)


#История приемов
class PatientWaitingAppointmentsAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomerRecord.objects.all()
    serializer_class = AppointmentWaitingHistorySerializer


#Оплата
class PatientPaymentReportView(generics.RetrieveAPIView):
    queryset = CustomerRecord.objects.all()
    serializer_class = PatientPaymentReportSerializer


#Данные пациента
class InfoPatientApiView(generics.RetrieveAPIView):
    queryset = Patient.objects.all()
    serializer_class = InformationPatientSerializer


#Список врачей
class DoctorsApiView(generics.ListAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorsSerializer


#Добавление врача
class DoctorCreateApiView(generics.CreateAPIView):
    serializer_class = DoctorCreateSerializer


# Сохранение врача
class DoctorSaveApiView(generics.UpdateAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSaveSerializer


#Подробный отчет
class DoctorAppointmentsApiView(generics.RetrieveAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorReportSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = [ 'department']
    search_fields = ['speciality']


#Сводный отчет
class SummaryReportClinicAPIView(APIView):

    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        records = CustomerRecord.objects.filter(records='был в приеме')

        if start_date and end_date:
            records = records.filter(date__date__range=[start_date, end_date])

        total_cash = records.filter(payment_type='cash').aggregate(Sum('price'))['price__sum'] or 0
        total_card = records.filter(payment_type='card').aggregate(Sum('price'))['price__sum'] or 0
        total_price = records.aggregate(Sum('price'))['price__sum'] or 0
        total_to_doctors = total_price  # или своя логика

        data = {
            "total_cash": total_cash,
            "total_card": total_card,
            "total_price": total_price,
            "total_to_doctors": total_to_doctors
        }

        serializer = SummaryReportSerializer(data)
        return Response(serializer.data)


# по врачам (процент врачу)
class DoctorReportListAPIView(generics.ListAPIView):
    serializer_class = DoctorReportSerializers
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields =  ['doctor', 'created_date']
    search_fields = ['patient']


    def get_queryset(self):
        qs = CustomerRecord.objects.select_related('doctor', 'patient', 'service')
        return self.filter_queryset(qs)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        response = super().list(request, *args, **kwargs)

        # Расчёт доли врача: (price * doctor.bonus / 100)
        queryset_with_bonus = queryset.annotate(
            doctor_income=ExpressionWrapper(
                F('price') * F('doctor__bonus') / 100.0,
                output_field=FloatField()
            )
        )

        total_doctor_income = queryset_with_bonus.aggregate(
            Sum('doctor_income')
        )['doctor_income__sum'] or 0

        # Ответ только с суммой врача и записями
        response.data = {
            'total_doctor_income': round(total_doctor_income, 2),
            'records': response.data
        }
        return response


# Управление календарем
class DoctorScheduleApiView(generics.ListAPIView):
    queryset = CustomerRecord.objects.all()
    serializer_class = AppointmentScheduleSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['doctor']


#Прайс лист
class PriceListApiView(generics.ListAPIView):
    queryset = Department.objects.all()
    serializer_class = PriceListSerializer