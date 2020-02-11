from random import choice
from datetime import datetime, timedelta
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import UserModel, UserInfo, CaptchaModel


class UserInfoListSerializer(serializers.ModelSerializer):
    """
    用户信息 序列化类 2
    """
    gender = serializers.CharField(help_text="性别")
    birthday = serializers.DateField(help_text="出生日期", format="%Y-%m-%d", required=False)
    mobile = serializers.CharField(help_text="手机")

    class Meta:
        model = UserInfo
        fields = ("gender", "birthday", "mobile", )


class UserListSerializer(serializers.ModelSerializer):
    """
    用户信息 序列化类 1
    """
    userinfo = UserInfoListSerializer(help_text="其他信息", read_only=True)
    first_name = serializers.CharField(help_text="姓")
    last_name = serializers.CharField(help_text="名")
    last_login = serializers.DateTimeField(help_text="最后登录时间", format="%Y-%m-%d %H:%M:%S", required=False)
    date_joined = serializers.DateTimeField(help_text="账户创建时间", format="%Y-%m-%d %H:%M:%S", required=False)
    is_active = serializers.BooleanField(help_text="是否可用")
    is_staff = serializers.BooleanField(help_text="是否为教师")

    class Meta:
        model = UserModel
        fields = ("id", "username", "first_name", "last_name", "last_login", "date_joined", "email", "userinfo", "is_active", "is_staff", )


class UserInfoUpdateSerializer(serializers.ModelSerializer):
    """
    用户信息修改 序列化类
    """
    email = serializers.EmailField(allow_blank=True, max_length=100, help_text="邮箱")
    first_name = serializers.CharField(allow_blank=True, max_length=4, help_text="姓")
    last_name = serializers.CharField(allow_blank=True, max_length=4, help_text="名")
    birthday = serializers.DateField(help_text="出生年月", allow_null=True)
    gender = serializers.ChoiceField(help_text="性别", choices=(("male", "男"), ("female", "女"), ("unknown", "未知")))
    mobile = serializers.CharField(allow_blank=True, max_length=11, help_text="电话")

    def validate_email(self, email):
        if len(email) == 0:
            return email
        if UserModel.objects.filter(email=email).count() and self.instance.email != email:
            raise serializers.ValidationError("该邮箱已被其他账户使用")
        return email

    def validate_mobile(self, mobile):
        if len(mobile) == 0:
            return mobile
        UserInfos = UserInfo.objects.filter(user=self.instance.id)
        if UserInfos.count():
            if UserInfos.first().mobile != mobile and UserInfo.objects.filter(mobile=mobile).count():
                raise serializers.ValidationError("该手机已被其他账户使用")
        elif UserInfo.objects.filter(mobile=mobile).count():
            raise serializers.ValidationError("该手机已被其他账户使用")
        return mobile

    class Meta:
        model = UserModel
        fields = ("email", "first_name", "last_name", "birthday", "gender", "mobile")


class UserResetPasswordSerializer(serializers.ModelSerializer):
    """
    用户重置密码 序列类
    """
    password = serializers.CharField(style={'input_type': 'password'}, help_text="密码", label="密码", write_only=True)

    def validate_password(self, password):
        import re
        flag = re.match(r'^[\S][^\u4e00-\u9fa5]{5,15}$', password)
        if flag is None:
            raise serializers.ValidationError({'error': '密码必须6到16位，且不能出现空格和汉字'})
        return password

    class Meta:
        model = UserModel
        fields = ("password", )


class UserResetPasswordMultipleSerializer(serializers.ModelSerializer):
    """
    用户密码修改 序列类
    """
    ids = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'}, help_text="密码", label="密码", write_only=True)

    def validate_ids(self, ids):
        ids_list = ids.split(',')
        for i in ids_list:
            users = UserModel.objects.filter(id=i)
            if users.count() == 0:
                raise serializers.ValidationError({'error': '操作失败：ID为' + i + '的用户不存在'})
        return ids

    def validate_password(self, password):
        import re
        flag = re.match(r'^[\S][^\u4e00-\u9fa5]{5,15}$', password)
        if flag is None:
            raise serializers.ValidationError({'error': '密码必须6到16位，且不能出现空格和汉字'})
        return password

    class Meta:
        model = UserModel
        fields = ("ids", "password", )


class UserRegSerializer(serializers.ModelSerializer):
    """
    用户注册序列化类
    """
    username = serializers.CharField(label="用户名", help_text="用户名", required=True, allow_blank=False,
                                     validators=[UniqueValidator(queryset=UserModel.objects.all(), message="用户已经存在")])
    password = serializers.CharField(style={'input_type': 'password'}, help_text="密码", label="密码", write_only=True)

    def create(self, validated_data):
        user = super(UserRegSerializer, self).create(validated_data=validated_data)
        user.set_password(validated_data["password"])
        user.save()
        return user

    class Meta:
        model = UserModel
        fields = ("username", "password")


class ChangePasswordSerializer(serializers.ModelSerializer):
    """
    用户密码修改序列类
    """
    username = serializers.CharField(read_only=True)
    code = serializers.CharField(required=True, write_only=True, max_length=6, min_length=6, label="验证码",
                                 error_messages={
                                     "blank": "请输入验证码",
                                     "required": "请输入验证码",
                                     "max_length": "验证码格式错误",
                                     "min_length": "验证码格式错误"
                                 },
                                 help_text="验证码")
    old_password = serializers.CharField(required=True, write_only=True, max_length=16, min_length=6, label="旧密码",
                                         error_messages={
                                             "blank": "请输入旧密码",
                                             "required": "请输入旧密码",
                                             "max_length": "旧密码格式错误",
                                             "min_length": "旧密码格式错误"
                                         },
                                         help_text="旧密码")
    new_password = serializers.CharField(required=True, write_only=True, max_length=16, min_length=6, label="新密码",
                                         error_messages={
                                             "blank": "请输入新密码",
                                             "required": "请输入新密码",
                                             "max_length": "新密码格式错误",
                                             "min_length": "新密码格式错误"
                                         },
                                         help_text="新密码")

    def validate_code(self, code):
        verify_user = self.context['request'].user
        verify_records = CaptchaModel.objects.filter(email=verify_user.email).order_by("-create_time")
        if verify_records:
            last_record = verify_records[0]
            five_mintes_ago = datetime.now() - timedelta(hours=0, minutes=5, seconds=0)
            if five_mintes_ago > last_record.create_time:
                raise serializers.ValidationError("验证码过期")
            if last_record.code != code:
                raise serializers.ValidationError("验证码错误")
        else:
            raise serializers.ValidationError("验证码不存在")
        if not verify_user.check_password(self.initial_data["old_password"]):
            raise serializers.ValidationError("旧密码错误")
        return code

    def update(self, instance, validated_data):
        user = self.context['request'].user
        user.set_password(validated_data["new_password"])
        user.save()
        return user

    def validate(self, attrs):
        attrs['username'] = self.context['request'].user.username
        del attrs["code"]
        return attrs

    class Meta:
        model = UserModel
        fields = ("username", "code", "old_password", "new_password")


class ChangeEmailSerializer(serializers.ModelSerializer):
    """
    用户邮箱修改序列化类
    """
    code = serializers.CharField(required=True, write_only=True, max_length=6, min_length=6, label="验证码",
                                 error_messages={
                                     "blank": "请输入验证码",
                                     "required": "请输入验证码",
                                     "max_length": "验证码格式错误",
                                     "min_length": "验证码格式错误"
                                 },
                                 help_text="验证码")
    email = serializers.EmailField(max_length=100, help_text="邮箱")

    def validate_email(self, email):
        if UserModel.objects.filter(email=email).count():
            raise serializers.ValidationError("该邮箱已被其他账户使用")
        return email

    def validate_code(self, code):
        verify_records = CaptchaModel.objects.filter(email=self.initial_data["email"]).order_by("-create_time")
        if verify_records:
            last_record = verify_records[0]
            five_mintes_ago = datetime.now() - timedelta(hours=0, minutes=5, seconds=0)
            if five_mintes_ago > last_record.create_time:
                raise serializers.ValidationError("验证码过期")
            if last_record.code != code:
                raise serializers.ValidationError("验证码错误")
        else:
            raise serializers.ValidationError("验证码错误")
        return code

    def validate(self, attrs):
        if attrs["email"] is None:
            attrs["email"] = self.initial_data["email"]
        del attrs["code"]
        return attrs

    class Meta:
        model = UserModel
        fields = ("email", "code",)


class VerifyCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, email):
        """
        验证邮箱是否已被使用
        """

        # 邮箱是否注册(因修改密码处发送验证码为同一接口，检测邮箱是否已注册放入修改邮箱处进行判断)
        # if UserModel.objects.filter(email=email).count():
        #     raise serializers.ValidationError("该邮箱已被使用")

        # 验证邮箱是否合法
        # EmailField自带验证，无需另外写

        # 验证码发送频率
        one_mintes_ago = datetime.now() - timedelta(hours=0, minutes=1, seconds=0)
        if CaptchaModel.objects.filter(create_time__gt=one_mintes_ago, email=email).count():
            raise serializers.ValidationError("距离上一次发送未超过一分钟")
        return email


class checkUserMailSerializer(serializers.Serializer):
    """
        检查用户邮箱 序列类
        Used for:
            checkUserMailViewset
    """
    email = serializers.EmailField(max_length=100, help_text="邮箱")

    class Meta:
        model = UserModel
        fields = ("email",)


class sendOldMailCaptchaSerializer(serializers.Serializer):
    """
        向旧邮箱发送验证码 序列类
        Used for:
            sendOldMailCaptchaViewset
    """
    email = serializers.EmailField(max_length=100, help_text="邮箱")

    def validate_email(self, email):
        one_mintes_ago = datetime.now() - timedelta(hours=0, minutes=1, seconds=0)
        if CaptchaModel.objects.filter(create_time__gt=one_mintes_ago, email=email).count():
            raise serializers.ValidationError("距离上一次发送未超过一分钟")
        return email

    class Meta:
        model = UserModel
        fields = ("email",)


class confirmMailCaptchaSerializer(serializers.Serializer):
    """
        确认邮箱验证码是否正确 序列类
        Used for:
            confirmOldMailCaptchaViewset
            confirmNewMailCaptchaViewset
    """
    email = serializers.EmailField(max_length=100, help_text="邮箱")
    code = serializers.CharField(required=True, write_only=True, max_length=6, min_length=6, label="验证码",
                                 error_messages={
                                     "blank": "请输入验证码",
                                     "required": "请输入验证码",
                                     "max_length": "验证码格式错误",
                                     "min_length": "验证码格式错误"
                                 },
                                 help_text="验证码")

    def validate_code(self, code):
        captcha = CaptchaModel.objects.filter(email=self.initial_data["email"]).order_by("-create_time")
        if captcha:
            last_captcha = captcha[0]
            five_mintes_ago = datetime.now() - timedelta(hours=0, minutes=5, seconds=0)
            if five_mintes_ago > last_captcha.create_time:
                raise serializers.ValidationError({'detail': '该验证码已过期'})
            if last_captcha.code != code:
                raise serializers.ValidationError({'detail': '该验证码错误'})
        else:
            raise serializers.ValidationError({'detail': '该邮箱的验证码不存在'})
        return code

    class Meta:
        model = UserModel
        fields = ("email", "code")


class sendNewMailCaptchaSerializer(serializers.Serializer):
    """
        向新邮箱发送验证码 序列类
        Used for:
            sendNewMailCaptchaViewset
    """
    email = serializers.EmailField(max_length=100, help_text="新邮箱")

    def validate_email(self, email):
        """
        验证邮箱
        """
        # 邮箱是否被使用
        if UserModel.objects.filter(email=email).count():
            raise serializers.ValidationError({'detail': '该邮箱已被使用'})
        # 验证码发送频率
        one_mintes_ago = datetime.now() - timedelta(hours=0, minutes=1, seconds=0)
        if CaptchaModel.objects.filter(create_time__gt=one_mintes_ago, email=email).count():
            raise serializers.ValidationError({'detail': '距离上一次发送未超过一分钟'})
        return email

    class Meta:
        model = CaptchaModel
        fields = ("email",)
