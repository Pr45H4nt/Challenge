from rest_framework import serializers
from pages.models import *
from authapp.models import CustomUser , Profile
from pages.models import Room, Session, Todo, SessionRanking
from stats.models import Notice


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()

    def get_username(self, inst):
        return str(inst.user.username)

    class Meta:
        model = Profile
        fields = '__all__'
        read_only_fields = ['user']


    def to_representation(self, instance):
        repr = super().to_representation(instance)
        if self.context.get('hide_user'):
            repr.pop('user', None)
        return repr
    
    def validate(self, attrs):
        request = self.context.get('request')
        attrs['user'] = request.user
        return super().validate(attrs)
    


class CustomUserSerializer(serializers.ModelSerializer):
    total_hours = serializers.ReadOnlyField()
    password = serializers.CharField(write_only=True)
    profile = serializers.SerializerMethodField()

    def get_profile(self, inst):
        profile_inst = getattr(inst, 'profile', None)
        if profile_inst:
            data = ProfileSerializer(profile_inst, context = {'hide_user': True}).data
            return data

        
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = CustomUser(**validated_data)
        if password:
            user.set_password(password)
        else:
            raise serializers.ValidationError("Password can't be empty")
        
        user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        
        for attr , value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)
        else:
            raise serializers.ValidationError("Password can't be empty")

        return instance


    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'password', 'age', 'last_online', 'total_hours', 'profile']
        read_only_fields = ['last_online', 'total_hours', ]


class RoomSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only = True, required=False)
    locked = serializers.SerializerMethodField()
    admin = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = '__all__'
        read_only_fields = ['created_on', 'total_hours']
    
    def get_locked(self, obj):
        if obj.password:
            return True
        return False
    
    def get_admin(self, obj):
        return str(obj.admin.username)
    
    def get_members(self, obj):
        members = [i.username for i in obj.members.all()]
        return members
    
    def create(self, validated_data):
        validated_data['admin'] = self.context.get('request').user
        members = [validated_data['admin']]
        room = super().create(validated_data)
        room.members.set(members)
        return room
    


class SessionSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField()
    start_date = serializers.ReadOnlyField()
    finish_date = serializers.ReadOnlyField()
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all())
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = Session
        fields = '__all__'

    def get_members(self, obj):
        members = [i.username for i in obj.members.all()]
        return members
    
    
    def validate(self, attrs):
        room = attrs.get('room')
        user = self.context.get('request').user
        if room and room.admin != user:
            raise serializers.ValidationError("You are not the admin of the room")
        return attrs
    
    

class RoomRankingSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    class Meta:
        model = RoomRanking
        exclude = ['room']

class SessionRankingSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    class Meta:
        model = SessionRanking
        exclude = ['session']

class TodoSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    is_due = serializers.ReadOnlyField()
    filledtoday = serializers.ReadOnlyField()
    total_hours = serializers.ReadOnlyField()
    session = serializers.PrimaryKeyRelatedField(queryset=Session.objects.all())
    is_session_active = serializers.SerializerMethodField()

    class Meta:
        model = Todo
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_on','completed', 'completed_on']

    def get_is_session_active(self, obj):
        return obj.session.is_active

    def validate_session(self, value):
        session = value
        if not getattr(session, 'is_active'):
            raise serializers.ValidationError("Session is not active")
        if self.instance and self.instance.session != value:
            raise serializers.ValidationError("Session cannot be modified")
        return value
    

    def create(self, validated_data):
        user = self.context.get('request').user
        if user.is_authenticated:
            validated_data['user'] = user
        return super().create(validated_data)   
    



class TrackTodoSerializer(serializers.ModelSerializer):
    todo = serializers.SerializerMethodField()
    session = serializers.SerializerMethodField()

    class Meta:
        model = TrackTodo
        fields = '__all__'

    def get_todo(self, obj):
        repr = {
            'id': obj.todo.id,
            'name' : obj.todo.task,
        }
        return repr
    
    def get_session(self, obj):
        repr = {
            'id': obj.todo.session.id,
            'name' : obj.todo.session.name,
        }
        return repr
    

    def to_representation(self, instance):
        repr= super().to_representation(instance)
        if self.context.get('hide_todo'):
            repr.pop('todo')
        return repr




class NoticeSerializer(serializers.ModelSerializer):
    room = serializers.SerializerMethodField()
    room_id = serializers.PrimaryKeyRelatedField(queryset = Room.objects.none(),write_only=True, source='room')
    author = serializers.SerializerMethodField()
    is_posted_today = serializers.ReadOnlyField()
    

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request:
            self.fields['room_id'].queryset = Room.objects.filter(members=request.user)


    
    class Meta:
        model = Notice
        fields = '__all__'
        read_only_fields = ['created_on', 'is_html']

    def get_room(self, obj):

        repr = {
            'id': obj.room.id,
            'name' : obj.room.name,
            'admin' : obj.room.admin.username
        }
        return repr
    
    def get_author(self, obj):
        return getattr(obj.author, 'username', None)
    
    def validate(self, attrs):
        request = self.context.get('request')
        is_admin = attrs.get('is_admin')
        is_pinned = attrs.get('is_pinned')
        room = attrs.get('room')
        
        if (is_admin or is_pinned) and room.admin != request.user:
            raise serializers.ValidationError("You are not the admin!")
        attrs['author'] = request.user
        return super().validate(attrs)

    
        
