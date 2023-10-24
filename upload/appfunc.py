import socket, sys,yaml
import base64,json,hmac,time,datetime
from hashlib import sha1 as sha
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import MD5
from Crypto.PublicKey import RSA
import urllib.request

# lambda fucntions
get_iso_8601 = lambda expire: datetime.datetime.utcfromtimestamp(expire).isoformat()+"Z"
get_http_request_unquote = lambda url: urllib.request.unquote(url)
get_pub_key = lambda pub_key_url_base64: urllib.request.urlopen((base64.b64decode(pub_key_url_base64.encode())).decode()).read()

def load_yaml(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


def get_local_ip():
    """
    获取本机 IPV4 地址
    :return: 成功返回本机 IP 地址，否则返回空
    """
    try:
        csocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        csocket.connect(('8.8.8.8', 80))
        (addr, port) = csocket.getsockname()
        csocket.close()
        return addr
    except socket.error:
        return ""


def get_token(config):
    now = int(time.time())
    expire_syncpoint = now + config['expire_time']
    expire = get_iso_8601(expire_syncpoint)

    policy_dict = {}
    policy_dict['expiration'] = expire
    condition_array = []
    array_item = []
    array_item.append('starts-with')
    array_item.append('$key')
    array_item.append(config['upload_dir'])
    condition_array.append(array_item)
    policy_dict['conditions'] = condition_array
    policy = json.dumps(policy_dict).strip()
    policy_encode = base64.b64encode(policy.encode())
    h = hmac.new(config['access_key_secret'].encode(), policy_encode, sha)
    sign_result = base64.encodestring(h.digest()).strip()

    callback_dict = {}
    callback_dict['callbackUrl'] = config['callback_url']
    callback_dict['callbackBody'] = 'filename=${object}&size=${size}&mimeType=${mimeType}' \
                                    '&height=${imageInfo.height}&width=${imageInfo.width}'
    # callback_dict['callbackBodyType'] = 'application/x-www-form-urlencoded'
    callback_dict['callbackBodyType'] = 'application/json'
    callback_param = json.dumps(callback_dict).strip()
    base64_callback_body = base64.b64encode(callback_param.encode())

    token_dict = {}
    token_dict['accessid'] = config['access_key_id']
    token_dict['host'] = config['host']
    token_dict['policy'] = policy_encode.decode()
    token_dict['signature'] = sign_result.decode()
    token_dict['expire'] = expire_syncpoint
    token_dict['dir'] = config['upload_dir']
    token_dict['callback'] = base64_callback_body.decode()
    result = json.dumps(token_dict)
    return result

def verrify(auth_str, authorization_base64, pub_key):
        """
        校验签名是否正确（MD5 + RAS）
        :param auth_str: 文本信息
        :param authorization_base64: 签名信息
        :param pub_key: 公钥
        :return: 若签名验证正确返回 True 否则返回 False
        """
        pub_key_load = RSA.importKey(pub_key)
        auth_md5 = MD5.new(auth_str.encode())
        result = False
        try:
            result = PKCS1_v1_5.new(pub_key_load).verify(auth_md5, base64.b64decode(authorization_base64.encode()))
        except Exception as e:
            print(e)
            result = False
        return result

def do_POST(request):
    print("********************* do_POST ")

    try:
        pub_key_url_base64 = request.headers['x-oss-pub-key-url']
        pub_key = get_pub_key(pub_key_url_base64)
    except Exception as e:
        print(str(e))
        print('Get pub key failed! pub_key_url : ' + pub_key_url)
        return False

    authorization_base64 = request.headers['authorization']

    content_length = request.headers['content-length']
    callback_body = request.body  # Updated this line for Django

    auth_str = ''
    pos = request.path.find('?')
    if -1 == pos:
        auth_str = request.path + '\n' + callback_body.decode()
    else:
        auth_str = get_http_request_unquote(request.path[0:pos]) + request.path[pos:] + '\n' + callback_body

    result = verrify(auth_str, authorization_base64, pub_key)

    if not result:
        print('Authorization verify failed!')
        print('Public key : %s' % (pub_key))
        print('Auth string : %s' % (auth_str))
        return False

    return True


