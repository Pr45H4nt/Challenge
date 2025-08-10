from .serializers import (
    CustomUserSerializer, ProfileSerializer, RoomSerializer, RoomRankingSerializer,
    SessionSerializer, SessionRankingSerializer, TodoSerializer, TrackTodoSerializer,
    NoticeSerializer
    )
from pages.models import Session, Room, Todo, RoomRanking, SessionRanking, TrackTodo
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from .serializers import CustomUser, Profile
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.renderers import JSONRenderer
from .permissions import IsAdmin, ActiveSession
from rest_framework.permissions import IsAuthenticated
from pages.logics import *
from django.contrib.auth import logout, login, authenticate


class UserAPI(APIView):
    renderer_classes = [JSONRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = CustomUserSerializer(request.user).data
        return Response(data)
    
    def post(self, request):
        data = request.data
        serializer = CustomUserSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({'message': 'Error while creating object'}, status=status.HTTP_400_BAD_REQUEST)
    
# if used session instead of jwt
class LogoutAPI(APIView):
    renderer_classes = [JSONRenderer]
    permission_classes = [IsAuthenticated]
    http_method_names = ['post']

    def post(self, request):
        logout(request)
        return Response({'Success': 'sucessfully logged out'})

# if used session instead of jwt
class LoginAPI(APIView):
    http_method_names = ['post']
    renderer_classes = [JSONRenderer]


    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({'Error': 'Username and password required'}, status=400)

        if request.user.is_authenticated:
            return Response({'Status': 'Already logged in'})
        user = authenticate(username=username, password=password)
        if user:
            login(request,user)
            return Response({'Success': 'successfully logged in'})
        return Response({'Error': 'Credentials wrong or not provided'}, status=status.HTTP_401_UNAUTHORIZED)
    



class ProfileAPI(ModelViewSet):
    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()
    http_method_names = ['get', 'post', 'put', 'patch']
    renderer_classes = [JSONRenderer]
    permission_classes = [IsAuthenticated]


    @action(detail=False, methods=['get'], url_path='me', url_name='my-profile')
    def get_own_profile(self, request, *args, **kwargs):
        obj = getattr(request.user, 'profile', None)
        if obj:
            data = self.get_serializer(obj).data
            return Response(data)
        else:
            return Response({"message": "You don't have a profile"}, status=status.HTTP_404_NOT_FOUND)
        
    def list(self, request, *args, **kwargs):
        return Response({"message": "Not allowed"}, status=status.HTTP_400_BAD_REQUEST)
    
    
   
class RoomAPI(ModelViewSet):
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]
    queryset = Room.objects.none()
    http_method_names = ['get', 'post', 'patch', 'put', 'delete']
    renderer_classes = [JSONRenderer]


    def get_permissions(self):
        permissions = super().get_permissions()
        if self.action in ['destroy', 'partial_update', 'update', 'remove_user', 'transfer_admin']:
            permissions.append(IsAdmin())
        return permissions


    def get_queryset(self):
        queryset = Room.objects.filter(members=self.request.user)
        return queryset

    @action(detail=True, methods=['get'], url_path='rankings', url_name='room_rankings')
    def get_room_rankings(self, request, *args, **kwargs):
        data = RoomRankingSerializer(self.get_object().rankings.all(), many=True).data
        return Response(data)
    

    @action(detail=True, methods=['post'], url_path='remove', url_name='remove-user')
    def remove_user(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        room = self.get_object()
        if not user_id:
            return Response({'error': 'user_id is not passed'}, status=status.HTTP_400_BAD_REQUEST)
        
        user_exists = room.members.filter(id=user_id).exists()
        if not user_exists:
            return Response({'error': 'user_id is not a member'}, status=status.HTTP_400_BAD_REQUEST)
        if user_id == str(room.admin.id):
            return Response({'error': 'admin cannot be removed. Transfer the ownership to remove the user'}, status=status.HTTP_400_BAD_REQUEST)

        room.remove_member(user_id)
        notice_kick_from_room_logic(request,room, user_id)
        return Response({'success': 'user is removed from the room'})
    

    @action(detail=True, methods=['post'], url_name='leave', url_path='leave')
    def remove_me(self, request, *args, **kwargs):
        user = request.user
        room = self.get_object()
        if room.admin == request.user:
            return Response({'error': 'admin cannot be removed. Transfer the ownership to remove the user'}, status=status.HTTP_400_BAD_REQUEST)

        room.remove_member(user.id)
        notice_leave_room_logic(request, room)
        return Response({'success': 'you are removed from the room'})

    @action(detail=True, methods=['post'], url_name='transfer-admin', url_path='transfer-admin')
    def transfer_admin(self, request, *args, **kwargs):
        room = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id is not passed'}, status=status.HTTP_400_BAD_REQUEST)
        
        user_exists = room.members.filter(id=user_id).exists()
        if not user_exists:
            return Response({'error': 'user_id is not a member'}, status=status.HTTP_400_BAD_REQUEST)
        
        room.transfer_admin(user_id)
        notice_transfer_ownership_logic(request, room, user_id)
        return Response({'success': 'Admin is transferred'})
    
    @action(detail=True, methods=['get'], url_name='sessions', url_path='sessions')
    def get_sessions(self, request, *args, **kwargs):
        sessions = self.get_object().sessions.filter(members=request.user)
        data = SessionSerializer(sessions, many=True).data
        return Response(data)
    
    @action(detail=False, methods=['post'], url_name='join', url_path='join')
    def join_room(self, request, *args, **kwargs):
        name = request.data.get('name')
        password = request.data.get('password')
        room = get_object_or_404(Room, name=name)
        if room.check_pass(password):
            room.members.add(request.user)
            room.save()
            return Response({'success': 'you have joined the room'}, status=status.HTTP_200_OK) 
        
        return Response({'Error': 'Credentials wrong. Please check again.'}, status=status.HTTP_401_UNAUTHORIZED)


    def partial_update(self, request, *args, **kwargs):
        if 'members' in request.data or 'admin' in request.data:
            return Response({'error': 'members or admin editing is not allowed via patch'}, status=status.HTTP_400_BAD_REQUEST)
        return super().partial_update(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        if 'members' in request.data or 'admin' in request.data:
            return Response({'error': 'members or admin editing is not allowed via put'}, status=status.HTTP_400_BAD_REQUEST)
        return super().update(request, *args, **kwargs)
    

class SessionAPI(ModelViewSet):
    serializer_class = SessionSerializer
    queryset = Session.objects.none()
    http_method_names = ['get', 'post', 'put', 'patch']
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]


    def get_queryset(self):
        queryset = Session.objects.filter(members=self.request.user)
        return queryset
    
    def get_permissions(self):
        permission =  super().get_permissions()
        if self.action in ['remove_user', 'start_session', 'end_session', 'partial_update', 'partial_update', 'create']:  
            permission.append(IsAdmin())
        return permission
    
    @action(detail=True, methods=['get'], url_name='get-session-rankings', url_path='rankings' )
    def get_session_rankings(self, request, *args, **kwargs):
        rankings = self.get_object().rankings.all()
        data = SessionRankingSerializer(rankings, many=True).data
        return Response(data)
    
    @action(detail=True, methods=['post'], url_name='remove-user', url_path='remove' )
    def remove_user(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        session = self.get_object()
        if not user_id:
            return Response({'error': 'user_id should be provided'}, status=status.HTTP_400_BAD_REQUEST)
        user_exists = session.members.filter(id=user_id).exists()
        if not user_exists:
            return Response({'error': 'user is not a member'}, status=status.HTTP_400_BAD_REQUEST)
        
        if user_id == session.room.admin:
            return Response({'error': 'admin cannot be removed from a session'}, status=status.HTTP_400_BAD_REQUEST)

        session.remove_member(user_id)
        notice_kick_from_session_logic(request, session, user_id)
        return Response({"Success": "User is removed from the session"})
    
    
    @action(detail=True, methods=['post'], url_name='remove-me', url_path='remove-me' )
    def remove_me(self, request, *args, **kwargs):
        session = self.get_object()

        if request.user == session.room.admin:
            return Response({'error': 'admin cannot be removed from a session'}, status=status.HTTP_400_BAD_REQUEST)
        
        session.remove_member(request.user.id)
        notice_leave_session_logic(request,session)
        return Response({"Success": "you are removed from the session"})
    
    
    @action(detail=True, methods=['post'], url_name='start-session', url_path='start' )
    def start_session(self, request, *args, **kwargs):
        session = self.get_object()
        start_session_logic(request, session.id)
        return Response({"Success": "session started"})

    
    @action(detail=True, methods=['post'], url_name='end-session', url_path='end' )
    def end_session(self, request, *args, **kwargs):
        session = self.get_object()
        end_session_logic(request, session.id)
        return Response({"Success": "session ended"})

    @action(detail=True, methods=['get'], url_name='get-todos', url_path='todos' )
    def get_todos(self, request, *args, **kwargs):
        session = self.get_object()
        data = TodoSerializer(session.todos.all(), many=True).data
        return Response(data)
    
    @action(detail=True, methods=['get'], url_name='get-my-todos', url_path='my-todos' )
    def get_my_todos(self, request, *args, **kwargs):
        session = self.get_object()
        data = TodoSerializer(session.todos.filter(user=request.user), many=True).data
        return Response(data)
    

class TodoAPI(ModelViewSet):
    serializer_class = TodoSerializer
    queryset = Todo.objects.none()
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']
    renderer_classes = [JSONRenderer]


    def get_queryset(self):
        queryset = Todo.objects.filter(user=self.request.user)
        return queryset
    
    def get_permissions(self):
        permissions = super().get_permissions()
        if self.action in ['toggle_task', 'update', 'partial_update', 'destroy', 'create']:
            permissions.append(ActiveSession())
        return permissions
    
    @action(detail=True, methods=['get'], url_name='get-tracking', url_path='trackings')
    def get_tracking(self, request, *args, **kwargs):
        todo = self.get_object()
        data = TrackTodoSerializer(todo.tracking.all(), many=True, context={'hide_todo':True}).data
        return Response(data)
    
    @action(detail=True, methods=['post'], url_name='toggle', url_path='toggle')
    def toggle_task(self, request, *args, **kwargs):
        task = self.get_object()

        if task.user == request.user:
            task.completed = not task.completed
            task.completed_on = None
            task.save()
        if task.completed:
            task.completed_on = timezone.localdate()
            notice_toggle_task(request,task)
            return Response({'Success': "Task set to completed"})
        
        return Response({'Success': "Task set to uncompleted"})
        

class TrackTodoAPI(ModelViewSet):
    serializer_class = TrackTodoSerializer
    queryset = TrackTodo.objects.none()
    http_method_names = ['get']
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]


    def get_queryset(self):
        queryset = TrackTodo.objects.filter(todo__user= self.request.user).order_by('-day')
        return queryset


class NoticeAPI(ModelViewSet):
    serializer_class = NoticeSerializer
    queryset = Notice.objects.none()
    http_method_names = ['get', 'post', 'delete']
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]


    def get_permissions(self):
        permissions = super().get_permissions()
        if self.action in ['toggle_pin']:
            permissions.append(IsAdmin())
        return permissions

    def get_queryset(self):
        qs = Notice.objects.filter(room__members = self.request.user)
        return qs
    
    def destroy(self, request, *args, **kwargs):
        notice = self.get_object()
        if notice.author != request.user:
            return Response({"Error": "you are not the author of the notice."})
        return super().destroy(request, *args, **kwargs)


    @action(detail=True, methods=['post'], url_path='toggle-pin', url_name='toggle-name')
    def toggle_pin(self, request, *args, **kwargs):
        notice = self.get_object()
        if notice.is_pinned:
            notice.is_pinned = False
            notice.save()
            return Response({'Success': 'Notice unpinned'})
        else:
            notice.is_pinned = True
            notice.save()
            return Response({'Success': 'Notice pinned'})
        
