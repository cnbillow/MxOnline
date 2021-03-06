# -*- coding:utf-8 -*-
from django.shortcuts import render
from django.views.generic import View
from django.http import HttpResponse
from django.db.models import Q
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger

from .models import CourseOrg, CityDict, Teacher
from .forms import UserAskForm
from courses.models import Course
from operation.models import UserFavorite


# 课程机构首页
class OrgView(View):
    '''
    课程机构列表功能
    '''
    def get(self, request):

        current_page = "course_org"
        # 这是数据
        all_orgs = CourseOrg.objects.all()
        all_citys = CityDict.objects.all()
        # 机构搜索功能
        search_keywords = request.GET.get('keywords', "")
        if search_keywords:
            all_orgs = all_orgs.filter(Q(name__icontains=search_keywords)
                                       | Q(desc__icontains=search_keywords))
        # 热门机构按点击量排序，取前三个
        hot_orgs = all_orgs.order_by("-click_nums")[:3]
        # 这里是一个库，取参数会很顺利
        # 对学习人数  课程数进行排序
        sort = request.GET.get('sort', "")
        if sort:
            if sort == "students":
                all_orgs = all_orgs.order_by("-students")
            elif sort == "courses":
                all_orgs = all_orgs.order_by("-course_nums")
        # 城市 类别 筛选
        city_id = request.GET.get('city', "")
        ct = request.GET.get('ct', "")
        if city_id:
            all_orgs = all_orgs.filter(city_id=int(city_id))
        if ct:
            all_orgs = all_orgs.filter(category=ct)
        try:
            # 对课程机构进行分页，分页的页码
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        org_nums = all_orgs.count()
        # 分页的数据
        # objects = ['john', 'edward', 'josh', 'frank']
        p = Paginator(all_orgs, 5, request=request)
        # 这个变量就是这一页里面的内容
        orgs = p.page(page)

        return render(request, "org-list.html", {
            "all_orgs": orgs,
            "all_citys": all_citys,
            "org_nums": org_nums,
            "city_id": city_id,
            "ct": ct,
            "hot_orgs": hot_orgs,
            "sort": sort,
            "current_page": current_page
        })


class AddUserAskView(View):
    '''
    用户添加咨询
    '''
    def post(self, request):
        userask_form = UserAskForm(request.POST)
        if userask_form.is_valid():
            user_ask = userask_form.save(commit=True)
            return HttpResponse('{"status":"success"}', content_type='application/json')
        else:
            return HttpResponse('{"status":"fail", "msg": "添加出错"}', content_type='application/json')


class OrgHomeView(View):
    '''
    课程详情页
    '''
    def get(self, request, org_id):
        current_page = "home"
        course_org = CourseOrg.objects.get(id=int(org_id))
        course_org.click_nums += 1
        course_org.save()
        has_fav = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True
        all_courses = course_org.course_set.all()[:3]
        all_teacher = course_org.teacher_set.all()[:3]
        return render(request, 'org-detail-homepage.html', {
            'all_courses': all_courses,
            'all_teacher': all_teacher,
            'course_org': course_org,
            'current_page': current_page,
            'has_fav': has_fav,
        })


class OrgCourseView(View):
    '''
    机构课程列表页
    '''
    def get(self, request, org_id):
        current_page = "course"
        course_org = CourseOrg.objects.get(id=int(org_id))
        has_fav = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True
        all_courses = course_org.course_set.all()[:3]
        return render(request, 'org-detail-course.html', {
            'all_courses': all_courses,
            'course_org': course_org,
            'current_page': current_page,
            'has_fav': has_fav,
        })


class OrgDescView(View):
    '''
    机构介绍
    '''
    def get(self, request, org_id):
        current_page = "desc"
        course_org = CourseOrg.objects.get(id=int(org_id))
        has_fav = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True
        return render(request, 'org-detail-desc.html', {
            'course_org': course_org,
            'current_page': current_page,
            'has_fav': has_fav,
        })


class OrgTeacherView(View):
    '''
    机构讲师
    '''
    def get(self, request, org_id):
        current_page = "teacher"
        course_org = CourseOrg.objects.get(id=int(org_id))
        has_fav = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True
        all_teachers = course_org.teacher_set.all()
        return render(request, 'org-detail-teachers.html', {
            'course_org': course_org,
            'current_page': current_page,
            'all_teachers': all_teachers,
            'has_fav': has_fav,
        })


class AddFavView(View):
    '''
    用户收藏   取消收藏
    '''
    def post(self, request):
        # 获取收藏的数据
        fav_id = request.POST.get('fav_id', 0)
        fav_type = request.POST.get('fav_type', 0)
        # 如果用户未登录
        if not request.user.is_authenticated():
            return HttpResponse('{"status":"fail", "msg": "用户未登录"}', content_type='application/json')
        exist_records = UserFavorite.objects.filter(user=request.user, fav_id=int(fav_id), fav_type=int(fav_type))
        if exist_records:
            # 如果记录已经存在，则认为是用户想取消收藏
            exist_records.delete()
            # 收藏数减1
            if int(fav_type) == 1:
                course = Course.objects.get(id=int(fav_id))
                course.fav_nums -= 1
                # 避免负数的情况
                if course.fav_nums < 0:
                    course.fav_nums = 0
                course.save()
            elif int(fav_type) == 2:
                org = CourseOrg.objects.get(id=int(fav_id))
                org.fav_nums -= 1
                if org.fav_nums < 0:
                    org.fav_nums = 0
                org.save()
            elif int(fav_type) == 3:
                teacher = Teacher.objects.get(id=int(fav_id))
                teacher.fav_nums -= 1
                if teacher.fav_nums < 0:
                    teacher.fav_nums = 0
                teacher.save()
            return HttpResponse('{"status":"success", "msg": "收藏"}', content_type='application/json')
        else:
            user_fav = UserFavorite()
            # 如果记录不存在的话，在保存之前就要判断是否需要为0
            if int(fav_id) > 0 and int(fav_type) > 0:
                user_fav.user = request.user
                user_fav.fav_id = int(fav_id)
                user_fav.fav_type = int(fav_type)
                user_fav.save()
                # 收藏数加1
                if int(fav_type) == 1:
                    course = Course.objects.get(id=int(fav_id))
                    course.fav_nums += 1
                    course.save()
                elif int(fav_type) == 2:
                    org = CourseOrg.objects.get(id=int(fav_id))
                    org.fav_nums += 1
                    org.save()
                elif int(fav_type) == 3:
                    teacher = Teacher.objects.get(id=int(fav_id))
                    teacher.fav_nums += 1
                    teacher.save()
                return HttpResponse('{"status":"success", "msg": "已收藏"}', content_type='application/json')
            else:
                return HttpResponse('{"status":"fail", "msg": "收藏出错"}', content_type='application/json')


class TeacherListView(View):
    '''
    所有讲师列表页
    '''
    def get(self, request):
        all_teachers = Teacher.objects.all()
        # 教师搜索功能,根据讲师名字，所属机构，职位
        search_keywords = request.GET.get('keywords', "")
        if search_keywords:
            all_teachers = all_teachers.filter(Q(name__icontains=search_keywords)
                                               | Q(org__name__icontains=search_keywords)
                                               | Q(work_position__icontains=search_keywords))

        sorted_teachers = all_teachers.order_by("-fav_nums")[:3]
        sort = request.GET.get('sort', "")
        if sort:
            if sort == "hot":
                all_teachers = all_teachers.order_by("-click_nums")
        try:
            # 对教师列表进行分页，获取分页的页码
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        teacher_nums = all_teachers.count()
        p = Paginator(all_teachers, 5, request=request)
        # 这个变量就是这一页里面的内容
        page_teachers = p.page(page)
        return render(request, "teachers-list.html", {
            "all_teachers": page_teachers,
            "teacher_nums": teacher_nums,
            "sort": sort,
            "sorted_teachers": sorted_teachers,

        })


class TeacherDetailView(View):
    def get(self, request, teacher_id):
        teacher = Teacher.objects.get(id=int(teacher_id))
        teacher.click_nums += 1
        teacher.save()
        teacher_has_fav = False
        org_has_fav = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user, fav_id=teacher_id, fav_type=3):
                teacher_has_fav = True
            if UserFavorite.objects.filter(user=request.user, fav_id=teacher.org.id, fav_type=2):
                org_has_fav = True
        all_teachers = Teacher.objects.all()
        sorted_teachers = all_teachers.order_by("-fav_nums")[:3]
        return render(request, "teacher-detail.html", {
            "teacher": teacher,
            "sorted_teachers": sorted_teachers,
            "teacher_has_fav": teacher_has_fav,
            "org_has_fav": org_has_fav,
        })

