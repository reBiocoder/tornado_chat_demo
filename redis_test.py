# import redis
#
# pool = redis.ConnectionPool(host='127.0.0.1', port='6379', decode_responses=True)
# r = redis.Redis(connection_pool=pool)
# r.set("name","zhoupeng")
#
# dic = {"a":1,"b":2,"c":3}
# r.lpush("def1",'{"a":"你好"}','{"b":"ok"}')
# print(r.lrange("def1",0,-1)[0])
# m= r.lrange("def1",0,-1)[0]
# print(eval(m))
import  time

a=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
print(a)






