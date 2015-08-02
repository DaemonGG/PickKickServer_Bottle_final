from bottle import route,get,post,run,static_file,request,response
import pymongo
import os
"""
@TODO:
    1. check connection status and retry
    2. 
"""


conn = pymongo.MongoClient('mongodb://localhost')
db   = conn.pickkick

class UserManage:
    """
    all the operations that manage user information and interacting with database
    """
    _field_username = 'username'
    _field_email = 'email'
    _field_passwd = 'pswd'

    def __init__(self):
        self._users = db.users

    def add_one_user(self,username,email,passwd):
        if self._users is None:
            print("Error: Unable to get users collection!")

        """ forbit duplicate username or email """
        checkDupQuery = {'$or':[{UserManage._field_username:username},{UserManage._field_email:email}]}
        check_res = self._users.find_one(checkDupQuery)

        if check_res is not None:
            return False

        doc = {UserManage._field_username: username,UserManage._field_email:email,UserManage._field_passwd:passwd}
        success=True
        try:
            self._users.insert_one(doc)
            pass
        except Exception as e:
            success=False
            print("Unexpected error:", type(e), e)
        return success

    def checkLogin(self,userInfoDic):
        if userInfoDic is None:
            return False
        if UserManage._field_passwd not in userInfoDic or (UserManage._field_email not in userInfoDic and UserManage._field_username not in userInfoDic):
            return False
        if self._users is None:
            print("Error: Unable to get users collection!")

        success = True
        try:
            doc = self._users.find_one(userInfoDic)
            if doc is None:
                success=False
                pass
            pass
        except Exception as e:
            success = False
            print("Login error:", type(e), e)
        return success

    def deleteOneUser(self,identity):
        if self._users is None:
            print("Error: Unable to get users collection!")

        query = {'$or':[{UserManage._field_username:identity},{UserManage._field_email:identity}]}
        try:
            self._users.delete_one(query)
            pass
        except Exception as e:
            print("Delete user error:", type(e), e)
    

       
@get('/download/<filename:path>')
def do_download(filename):
    response = static_file(filename,root = './property/')
    response.set_header('Content-Disposition','attachment; filename=\"'+filename+'\"')
    #filename = request.forms.get('download_file')
    return  response

@post('/uploads')
def do_upload():
    for key in request.headers.keys():
        print(key+': '+request.headers.get(key))
    upload     = request.files.get('image')
    time       = request.forms.get('time')
    print('TIME FROM PHOTO  '+time)

    name, ext = os.path.splitext(upload.filename)
    print('FILE NAME: '+name+ext)

    if ext not in ('.png','.jpg','.jpeg'):
        return 'File extension not allowed.'
    save_path = "./property/"+upload.filename
    upload.save(save_path)
    return 'OK'

@route('/testpost',method='post')
def test_output():
    clen = request.content_length
    data = request.body.read(clen)
    print(data)
    return 'OK'



if __name__=='__main__':
    hr = UserManage()
    hr.add_one_user('xing','xing@hotmail.com','hsajkdfhksaljdf')

    if hr.add_one_user('xingchi','xingchij@hotmail.com','hsajkdfhksaljdf'):
        print('check fail')
        pass

    hr.deleteOneUser('xingchi')
    hr.deleteOneUser('xing@hotmail.com')
    # login = {'username':'xingchi','pswd':'hsajkdfhksaljdf'}
    # if hr.checkLogin(login) is True:
    #     print('Success')
    #     pass
    # else:
    #     print('no')
    #run(host='192.168.191.1',port=8080,debug=True)

