# coding:utf-8
import time

from openstack.middleware.common.common import send_request, IP_keystone, PORT_keystone, plog,cache
from openstack.middleware.common.urls import url_get_token,url_project_id
from user_auth.models import Account

token_dict = {}
project_id_dict = {}
user_token_dict = {}
admin_token_dict = {"admin_token":"","time":0}
admin_project_id = ""
admin_user_token = ""


class Login:
    def __init__(self, name, password):
        self.token = ""
        self.project_id = ""
        self.user_token = ""
        self.name = name
        self.password = password

    @plog("Login.get_user_token")
    def user_token_login(self):
        '''
        得到一个用户的token，但是没有对项目相关操作的权限
        :return:
        '''
        global user_token_dict
        ret = 0
        cache(username=self.name)
        method = "POST"
        path = url_get_token
        params = {
            "auth":
                {
                    "identity":
                        {
                            "methods":
                                [
                                    "password"
                                ],
                            "password":
                                {
                                    "user":
                                        {
                                            "name": self.name,
                                            "domain": {
                                                "name": "default"
                                            },
                                            "password": self.password
                                        }
                                }
                        }
                }
        }
        cache(del_cache="*")   #切换用户时清除缓存
        head = {"Content-Type": "application/json"}
        ret = send_request(method, IP_keystone, PORT_keystone, path, params, head, flag=1)
        self.user_token = ret["token_id"]
        user_token_dict[self.name] = self.user_token
        return 0

    @plog("Login.get_proid")
    def proid_login(self,is_admin=False):
        '''
        得到project_id,为下面获取token作准备
        is_admin:如果为true，则表示是openstack admin用户登入，不能去数据库获取项目名称,项目名称为admin
        :return:
        '''
        global project_id_dict
        ret = 0
        if not is_admin:
            project_name = Account.objects.get(name=self.name).cur_space
        else:
            project_name = "admin"
        method = "GET"
        path = url_project_id
        params = ''
        head = {"X-Auth-Token": self.user_token}
        ret = send_request(method, IP_keystone, PORT_keystone, path, params, head)
        # self.project_id = ret["projects"][0].get("id", "")
        self.project_id = [i["id"] for i in ret["projects"] if i["name"] == project_name][0]
        project_id_dict[self.name] = self.project_id
        return 0

    @plog("Login.get_token")
    def token_login(self):
        '''
        得到能对项目操作的token
        :return:
        '''
        global token_dict
        ret = 0
        assert self.project_id != "", "proejct_id is none"
        method = "POST"
        path = url_get_token
        params = {
            "auth":
                {
                    "identity":
                        {
                            "methods":
                                [
                                    "password"
                                ],
                            "password":
                                {
                                    "user":
                                        {
                                            "name": self.name,
                                            "domain": {
                                                "name": "default"
                                            },
                                            "password": self.password
                                        }
                                }
                        },
                    "scope":
                        {
                            "project": {
                                "id": self.project_id
                            }
                        }
                }
        }
        head = {"Content-Type": "application/json"}
        ret = send_request(method, IP_keystone, PORT_keystone, path, params, head, flag=1)
        self.token = ret["token_id"]
        token_dict[self.name] = self.token
        return 0

def get_token():
    return token_dict

@plog("admin_login")
def admin_login(project_id_now=""):
    global admin_token_dict
    global user_token_dict
    global project_id_dict
    global token_dict
    global admin_project_id
    global admin_user_token
    admin_username = "admin"
    admin_password = "mbk3HwlMx8e"
    admin_handle = Login(admin_username,admin_password)
    admin_handle.user_token_login()
    admin_handle.proid_login(is_admin=True)
    if project_id_now:
        admin_handle.project_id = project_id_now
    admin_handle.token_login()
    admin_user_token = user_token_dict[admin_username]
    admin_token_dict["admin_token"] = token_dict[admin_username]
    admin_token_dict["time"] = int(time.time())
    admin_project_id = project_id_dict[admin_username]

@plog("get_admin_token")
def get_admin_token(project_id=""):
    if admin_token_dict["admin_token"] == "" or int(time.time() - admin_token_dict["time"]) >= 1800:
        admin_login(project_id)
    return admin_token_dict["admin_token"]

def get_admin_project_id():
    if admin_project_id == "":
        admin_login()
    return admin_project_id

def get_proid():
    return project_id_dict

def get_user_token():
    return user_token_dict

@plog("get_project")
def get_project(user_name):
    global user_token_dict
    user_token = user_token_dict[user_name]
    assert user_token != "", "not login"
    method = "GET"
    path = url_project_id
    params = ''
    head = {"X-Auth-Token": user_token}
    ret = send_request(method, IP_keystone, PORT_keystone, path, params, head)
    return ret

def login_out(username):
    global token_dict
    global project_id_dict
    token_dict[username] = ""
    project_id_dict[username] = ""


