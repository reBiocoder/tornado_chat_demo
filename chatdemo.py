from tornado import web,httpserver,options,ioloop
from tornado.locks import Condition,CancelledError
import redis
import  time
options.define("port",default=8888,help="default port")


def get_single_chat_key(sender_id, receiver_id):
    if sender_id <= receiver_id:
        single_chat_key = str(sender_id) + "-" + str(receiver_id)
    else:
        single_chat_key = str(receiver_id) + "-" + str(sender_id)
    return single_chat_key

class MessageCacheHandler(object):
    pool = redis.ConnectionPool(host="127.0.0.1", port="6379", decode_responses=True)
    r = redis.Redis(connection_pool=pool, charset="utf-8")

    def __init__(self):
        self.cond = Condition()
        self.cache = MessageCacheHandler.r
        self.MAX_CACHE_SIZE = 200

    def get_message_since(self,cursor,single_chat_key):
        result = self.cache.lrange(single_chat_key,0,-1)
        return list(result)

    def add_message(self, message, sender_id, receiver_id):
        single_chat_key = get_single_chat_key(sender_id, receiver_id)
        now_time = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
        cache_message_value = {"create_time": now_time, "message":  message, "sender": sender_id, "receiver_id": receiver_id}
        self.cache.rpush(single_chat_key,str(cache_message_value))
        self.cond.notify_all()


global_message_buffer = MessageCacheHandler()


class IndexHandler(web.RequestHandler):
    def get(self):
        sender_id = self.get_argument("sender_id",None)
        receiver_id = self.get_argument("receiver_id",None)
        if not sender_id or not receiver_id:
            self.write("无法进入")
        else:
            single_chat_key = get_single_chat_key(sender_id,receiver_id)
            message_list = global_message_buffer.cache.lrange(single_chat_key, 0, -1)
            self.write({"messageList": message_list})


class NewMessageHandler(web.RequestHandler):
    def get(self):
        sender_id = self.get_argument("sender_id",None)
        receiver_id = self.get_argument("receiver_id",None)
        message = self.get_arguments("message")
        if not sender_id or  not receiver_id:
            self.write("无法进入")
        else:
            global_message_buffer.add_message(message,sender_id,receiver_id)
            single_chat_key = get_single_chat_key(sender_id, receiver_id)
            message_list = global_message_buffer.cache.lrange(single_chat_key, 0, -1)
            self.write({"messageList": message_list})



class UpdateMessageHandler(web.RequestHandler):
    async def get(self):
            sender_id = self.get_argument("sender_id")
            receiver_id = self.get_argument("receiver_id")
            single_chat_key = get_single_chat_key(sender_id, receiver_id)
            cursor = self.get_arguments("cursor")
            message_list = []
            while not message_list:
                self.wait_future = global_message_buffer.cond.wait()
                print("等待开始")
                try:
                    await self.wait_future
                    print("等待结束")
                except CancelledError:
                      return
                message_list = global_message_buffer.get_message_since(cursor, single_chat_key)
            if self.request.connection.stream.closed():
                return
            self.write({"messageList": str(message_list)})
    def on_connection_close(self):
        self.wait_future.cancel()


def main():
    options.parse_command_line()
    app = web.Application([
        (r'/',IndexHandler),
        (r'/new',NewMessageHandler),
        (r'/update',UpdateMessageHandler)],
    debug=True
    )
    app.listen(8888)
    ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()




































