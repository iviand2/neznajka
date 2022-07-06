# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, '/var/www/u0600623/data/www/nnk.el-pro.ru/neznajka')
sys.path.insert(1, '/var/www/u0600623/data/djangoenv/lib/python3.9/site-packages')
os.environ['DJANGO_SETTINGS_MODULE'] = 'neznajka.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
# import os
# import sys
# from django.core.wsgi import get_wsgi_application
#
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neznajka.settings')
# sys.path.insert(0, '/var/www/u0600623/data/www/nnk.el-pro.ru')
# sys.path.insert(1, '/var/www/u0600623/data/djangoenv/lib/python3.9/site-packages')
#
# application = get_wsgi_application()
