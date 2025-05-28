from rest_framework import viewsets, generics, status, permissions, serializers
from .serializers import *
from .models import *
from django.db.models import Count, Q, Sum, F, FloatField, ExpressionWrapper
from .filters import *
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////
from rest_framework import viewsets, generics, status
from .serializers import *
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response


class UserProfileRegisterView(generics.CreateAPIView):
    serializer_class = UserProfileRegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer=self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user=serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DoctorRegisterView(generics.CreateAPIView):
    serializer_class = DoctorRegisterSerializer


class ReceptionRegisterView(generics.CreateAPIView):
    serializer_class = ReceptionRegisterSerializer


class CustomLoginView(TokenObtainPairView):
    serializer_class = LoginSerializers

    def post(self, request, *args, **kwargs):
        serializer=self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response({"detail: Неверные учетные данные"}, status=status.HTTP_401_UNAUTHORIZED)

        user=serializer.validated_data
        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomAdminLoginView(TokenObtainPairView):
    serializer_class = LoginSerializers

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


class CustomerRecordListAPIView(generics.ListAPIView):
    queryset = CustomerRecord.objects.all()
    serializer_class = CustomerRecordListSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = CustomerRecordListFilter
    search_fields = ['patient']


class CustomerRecordCreateAPIView(generics.CreateAPIView):
    queryset = CustomerRecord.objects.all()
    serializer_class = CustomerRecordCreateSerializer


class CustomerRecordRetrieveAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomerRecord.objects.all()
    serializer_class = CustomerRecordListSerializer


class CustomerRecordRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomerRecord.objects.all()
    serializer_class = CustomerRecordListSerializer


class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorListSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = DoctorListFilter
    search_fields = ['doctor'] 


class AboutPatientRecordListAPIView(generics.ListAPIView):
    queryset = CustomerRecord.objects.all()
    serializer_class = AboutPatientRecordSerializer


class AboutPatientRecordListUpdateAPIView(generics.RetrieveUpdateAPIView):
    queryset = CustomerRecord.objects.all()
    serializer_class = AboutPatientRecordSerializer


# class AboutPatientHistoryRecordListAPIView(generics.ListAPIView):
#     queryset = CustomerRecord.objects.all()
#     serializer_class = AboutPatientHistoryRecordSerializer


class AboutPatientHistoryRecordListAPIView(generics.ListAPIView):
    queryset = CustomerRecord.objects.all()
    serializer_class = AboutPatientHistoryRecordSerializer

    def get_queryset(self):
        patient_id = self.kwargs['patient_id']
        return CustomerRecord.objects.filter(patient_id=patient_id)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serialized_data = self.get_serializer(queryset, many=True).data

        total_count = queryset.count()

        status_summary = queryset.values('status').annotate(count=Count('id'))

        return Response({
            "total_records": total_count,
            "status_summary": status_summary,
            "records": serialized_data
        })


class PatientRecordListAPIView(generics.ListAPIView):
    serializer_class = AboutPatientHistoryRecordSerializer

    def get_queryset(self):
        patient_id = self.kwargs['patient_id']
        return CustomerRecord.objects.filter(patient_id=patient_id, records='был в приеме')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serialized_data = self.get_serializer(queryset, many=True).data

        total_count = queryset.count()

        status_summary = queryset.values('status').annotate(count=Count('id'))

        return Response({
            "total_records": total_count,
            "status_summary": status_summary,
            "records": serialized_data
        })


class AboutPatientHistoryListAPIView(generics.ListAPIView):
    queryset = CustomerRecord.objects.all()
    serializer_class = AboutPatientHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return CustomerRecord.objects.filter(patient=user)


class PaymentListAPIView(APIView):
    queryset = CustomerRecord.objects.all()
    serializer_class = PaymentSerializer

    def get(self, request, patient_id):
        queryset = CustomerRecord.objects.filter(patient_id=patient_id)

        total_paid = queryset.aggregate(total=Sum('price'))['total'] or 0
        cash_paid = queryset.filter(payment_type='cash').aggregate(cash=Sum('price'))['cash'] or 0
        card_paid = queryset.filter(payment_type='card').aggregate(card=Sum('price'))['card'] or 0

        serialized_data = PaymentSerializer(queryset, many=True).data

        return Response({
            "total_paid": total_paid,
            "cash_paid": cash_paid,
            "card_paid": card_paid,
            "records": serialized_data
        })


class InfoPatientListAPIView(generics.ListAPIView):
    queryset = Patient.objects.all()
    serializer_class = InfoPatientSerializer


class PriceListAPIView(generics.ListAPIView):
    queryset = Service.objects.all()
    serializer_class = PriceListSerializer


class PriceDetailAPIView(generics.RetrieveAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceDetailSerializer


class DetailedReportListAPIView(generics.ListAPIView):
    queryset = CustomerRecord.objects.all()
    serializer_class = DetailedReportSerializer
    # filter_backends = [DjangoFilterBackend, SearchFilter]
    # filterset_class = DetailedRecordListFilter
    # search_fields = ['patient']

    def get_queryset(self):
        qs = CustomerRecord.objects.select_related('doctor', 'patient', 'service')
        return self.filter_queryset(qs)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        response = super().list(request, *args, **kwargs)

        total_price = queryset.aggregate(Sum('price'))['price__sum'] or 0
        total_discount = queryset.aggregate(Sum('discount'))['discount__sum'] or 0
        total_count = queryset.count()

        cash_sum = queryset.filter(payment_type='cash').aggregate(Sum('price'))['price__sum'] or 0
        card_sum = queryset.filter(payment_type='card').aggregate(Sum('price'))['price__sum'] or 0

        queryset_with_bonus = queryset.annotate(
            doctor_income=ExpressionWrapper(
                F('price') * F('doctor__bonus') / 100.0,
                output_field=FloatField()
            )
        )

        doctor_income_total = queryset_with_bonus.aggregate(
            Sum('doctor_income')
        )['doctor_income__sum'] or 0

        response.data = {
            'total_count': total_count,
            'total_price': total_price,
            'total_discount': total_discount,
            'cash_sum': cash_sum,
            'card_sum': card_sum,
            'total_doctor_income': round(doctor_income_total, 2),
            'records': response.data
        }

        return response


class DoctorReportListAPIView(generics.ListAPIView):
    serializer_class = DoctorReportSerializers
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = CustomerRecordListFilter
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


class SummaryReportAPIView(APIView):

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


class CalendarViewSet(viewsets.ModelViewSet):
    queryset = CustomerRecord.objects.all()
    serializer_class = CalendarSerializer


