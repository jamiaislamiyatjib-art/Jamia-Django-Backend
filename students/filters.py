# import django_filters
# from django.db.models import Q
# from .models import Student

# class StudentFilter(django_filters.FilterSet):
#     session = django_filters.CharFilter(field_name='session', lookup_expr='exact')
#     student_class = django_filters.CharFilter(field_name='student_class', lookup_expr='exact')
#     search = django_filters.CharFilter(method='filter_search')

#     class Meta:
#         model = Student
#         fields = ['session', 'student_class']

#     def filter_search(self, queryset, name, value):
#         if value:
#             return queryset.filter(
#                 Q(student_name__icontains=value) |
#                 Q(student_id__icontains=value) |
#                 Q(roll_no__icontains=value) |
#                 Q(enroll_no__icontains=value) |
#                 Q(student_class__icontains=value) |
#                 Q(father_husband_name__icontains=value)
#             )
#         return queryset


# filters.py
import django_filters
from django.db.models import Q
from .models import Student

class StudentFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method="global_search")

    class Meta:
        model = Student
        fields = ['session', 'student_class', 'center']

    def global_search(self, queryset, name, value):
        return queryset.filter(
            Q(student_name__icontains=value) |
            Q(father_husband_name__icontains=value) |
            Q(student_id__icontains=value) |
            Q(roll_no__icontains=value) |
            Q(enroll_no__icontains=value) |
            Q(student_class__icontains=value) |
            Q(session__icontains=value) |
            Q(medium__icontains=value) |
            Q(city__icontains=value) |
            Q(place__icontains=value) |
            Q(center__center_name__icontains=value)
        )
