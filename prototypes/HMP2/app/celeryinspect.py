from celery.task.control import inspect

if __name__ == "__main__":
     i = inspect()
     print "REGISTERED TASKS:"
     print i.registered()