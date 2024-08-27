# -*- coding: UTF-8 -*-

'''
包含项目的一些配置
'''

deploy_target = 'test'  # 部署配置，可选择'test' or 'prod'

# 如果测试环境
if deploy_target == 'test':
    service_port = 9010   # 服务端口
    AUTH_ENABLED = False
    SECRET_KEY = "c2VjcmV0OmtleQ=="
    ENABLE_CORS = True    # 是否允许跨域

# 生产环境
else:
    service_port = 9010   # 服务端口
    AUTH_ENABLED = False
    SECRET_KEY = "c2VjcmV0OmtleQ=="
    ENABLE_CORS = True
    
