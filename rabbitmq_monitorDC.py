#! /usr/bin/python2
# -*- coding: utf-8 -*-
import urllib2
import json
import time
import smtplib
import optionsresolver
import logger as logger
import httplib
import os
import re
import sys
from telnetlib import theNULL


#Import InfluxDb module from mounted code
rootPath=r'/root/scripts/'
sys.path.append(rootPath)
influxPath=r'/root/scripts/core/'
sys.path.append(influxPath)
import influx

#Global Variables
jsonForInflux=[]
measurementTasks='rabbitmq_monitor'


class RabbitMQAlert:
    def __init__(self, log):
        self.log = log

    def check_queue_conditions(self, options, host, port, DC, influxDb=True):
        options["host"] = host
        options["port"] = port
        queue = options["queue"]
        url = "http://%s:%s/api/queues/%s/%s" % (options["host"], options["port"], options["vhost"], options["queue"])
        self.log.info("URL for Queue Conditions--  \"{0}\"".format(url))
        data = self.send_request(DC, url, options)
        if data is None:
            return

        messages_ready = data.get("messages_ready")
        messages_unacknowledged = data.get("messages_unacknowledged")
        
        messages = data.get("messages")
        consumers = data.get("consumers")
        queue_conditions = options["conditions"][queue]
        ready_size = queue_conditions.get("ready_queue_size")
        unack_size = queue_conditions.get("unack_queue_size")
        total_size = queue_conditions.get("total_queue_size")
        consumers_connected_min = queue_conditions.get("queue_consumers_connected_min")
        consumers_connected_max = queue_conditions.get("queue_consumers_connected_max")
        queue = options["queue"]
        queue_conditions = options["conditions"][queue]
        spark_room_id = queue_conditions.get("spark-room-id")
        print(spark_room_id)
        spark_bearer_id = queue_conditions.get("spark-bearer-id")
        print(spark_bearer_id)

        if ready_size is not None and messages_ready > ready_size:
            print("In send_notifications")
            self.send_notification(DC, options, "- <b>[ Alert - Queue -%s  ]</b> %s [ Condition: messages_ready = %d > %d ]" % (options['rabbitServerLocation'],queue, messages_ready, ready_size))
            print("send_notifications called")
        if unack_size is not None and messages_unacknowledged > unack_size:
            self.send_notification(DC, options, "- <b>[ Alert - Queue - %s  ]</b> %s [ Condition: messages_unacknowledged = %d > %d ]" % (options['rabbitServerLocation'],queue, messages_unacknowledged, unack_size))

        if total_size is not None and messages > total_size:
            self.send_notification(DC, options, "- <b>[ Alert - Queue - %s  ]</b> %s [ Condition:  messages = %d > %d ]" % (options['rabbitServerLocation'],queue, messages, total_size))

        if consumers_connected_min is not None and consumers < consumers_connected_min:
            self.send_notification(DC, options, "- <b>[ Alert - Queue - %s  ]</b> %s [ Condition: queue_consumers_connected = %d < %d ]" % (options['rabbitServerLocation'],queue, consumers, consumers_connected_min))
        if consumers_connected_max is not None and consumers > consumers_connected_max:
            self.send_notification(DC, options, "- <b>[ Alert - Queue -  %s  ]</b> %s [ Condition: queue_consumers_connected = %d > %d ]" % (options['rabbitServerLocation'],queue, consumers, consumers_connected_max))

        if influxDb:
            self.createJsonForInfluxQueue(messages_ready,messages_unacknowledged,messages,consumers,options,host,port,DC)


    def get_bindings_for_exchange(self,data , exName='',include_vpods=False):
        out=[]
        for item in data:
             if item['source']==exName:
                 if item['destination_type']=="queue":
                     if include_vpods:
                         out.append(item['destination'])
                     else: 
                         if "vpod" not in item['destination'] and "dpod" not in item['destination']:
                             out.append(item['destination'])
        return len(out), out 



    def get_data_for_exchanges(self, options, host, port, DC, influxDb=True):
        options["host"] = host
        options["port"] = port
        queue = options["queue"]
        exchange = options["exchanges"]
        exchangeurl = "http://%s:%s/api/bindings/%s" % (options["host"], options["port"], options["vhost"])
        print(exchangeurl)
    
        data = self.send_request(DC,exchangeurl,options)
        if data is None:
            return
        
        print("DATA...................................................................")
        print(data)
        print("DATA...................................................................")


        if exchange!='default':
            c,q=self.get_bindings_for_exchange(data,exName=exchange)
            #print("Exchange " + str(exchange) + " has " + str(c) + " binding(s): " +str(q) )
            #self.send_notification(DC, options, "<b>[ Debug - %s ]</b> [ Exchange: %s has %s  bindings %s ]" % (options['rabbitServerLocation'] ,str(exchange), str(c), str(q)))
            print""
        else:
            c,q=self.get_bindings_for_exchange(data)
            #self.send_notification(DC, options, "<b>[ Debug - %s ]</b> [Exchange: Default has %s bindings %s ]" % (options['rabbitServerLocation'] ,str(c),str(q)))
            #print("Exchange Default  has "+ str(c) + " binding(s): " +str(q) )
            print""

        if influxDb:
            self.createJsonForInfluxExchange(0,0,c,q,options,host,port,DC)
        

    def createJsonForInfluxQueue(self,messages_ready,messages_unacknowledged,messages,consumers,options,host,port,DC,measurement=measurementTasks):
        global jsonForInflux
        options["host"] = host
        options["port"] = port
        if host == "198.19.254.159" :
            to_monitor_host = DC
        if host == "dcv-automation-amqp.svpod.dc-01.com" :
            to_monitor_host = "RTP"
        if host == "dcv-automation-amqp.svpod.dc-02.com" :
            to_monitor_host = "SNG"
        if host == "dcv-automation-amqp.svpod.dc-03.com" :
            to_monitor_host = "LON"
        print("creating the json")
        try:
            jsonForInflux.append({"measurement":measurement,"tags":{"Monitor_location":DC,"Rabbitmq_server":to_monitor_host,"objectType":"queue","objectName":options["queue"]},"fields":{"msgReady": messages_ready,"msgUnack":messages_unacknowledged,"msgTotal":messages,"consumers":consumers}})
        except Exception as e:
            self.log.info('Error while reading the arguments...' )
        #self.send_notification(DC, options, "<b>[ Debug - %s ]</b>  [ JsonforInflux: %s ]" % (to_monitor_host,jsonForInflux))
        #influx.writeToInfluxDb(jsonForInflux,credsFile='/root/creds/creds.cfg',influxDb='influxGlobal',ssl=True, verify_ssl=True)
        print jsonForInflux
        return jsonForInflux



    def createJsonForInfluxExchange(self,rate_in,rate_out,binding_count,bindings,options,host,port,DC,measurement=measurementTasks):
        global jsonForInflux
        options["host"] = host
        options["port"] = port
        if host == "198.19.254.159" :
            to_monitor_host = DC
        if host == "dcv-automation-amqp.svpod.dc-01.com" :
            to_monitor_host = "RTP"
        if host == "dcv-automation-amqp.svpod.dc-02.com" :
            to_monitor_host = "SNG"
        if host == "dcv-automation-amqp.svpod.dc-03.com" :
            to_monitor_host = "LON"
        print("creating the json")

        for binding in bindings:
            try:
                jsonForInflux.append({"measurement":measurement,"tags":{"Monitor_location":DC,"Rabbitmq_server":to_monitor_host,"objectType":"exchange","objectName":options["exchanges"]},"fields":{"rateIn": rate_in,"rateOut":rate_out,"bindingTotal":binding_count,"binding":binding}})
            except Exception as e:
                self.log.info('Error while reading the arguments...' )

        if len(jsonForInflux)==0:
            jsonForInflux.append({"measurement":measurement,"tags":{"Monitor_location":DC,"Rabbitmq_server":to_monitor_host,"objectType":"exchange","objectName":options["exchanges"]},"fields":{"rateIn": rate_in,"rateOut":rate_out,"bindingTotal":0,"binding":"-"}})
            influx.writeToInfluxDb(jsonForInflux,credsFile='/root/creds/creds.cfg',influxDb='influxGlobal' ,ssl=True, verify_ssl=True)

        #self.send_notification(DC, options, "<b>[ Debug - %s ]</b>  [ JsonforInflux: %s ]" % (to_monitor_host,jsonForInflux))
        #influx.writeToInfluxDb(jsonForInflux,credsFile='/root/creds/creds.cfg',influxDb='influxGlobal' ,ssl=True, verify_ssl=True)
        print jsonForInflux



        return jsonForInflux





    def check_consumer_conditions(self, options,host,port,DC):        
        options["host"] = host
        options["port"] = port
        queue = options["queue"]
        url = "http://%s:%s/api/consumers" % (options["host"], options["port"])
        self.log.info("URL for Consumer Conditions--  \"{0}\"".format(url))
        data = self.send_request(DC, url, options)
        if data is None:
            return

        consumers_connected = len(data)
        print("check consumers_connected")
        consumers_connected_min = options["default_conditions"].get("consumers_connected")

        if consumers_connected is not None and consumers_connected < consumers_connected_min:
            self.send_notification(DC, options, "- <b>[ Alert - Queue - %s ]</b> %s [ Condition: default_consumers_connected = %d < %d ]" % (options['rabbitServerLocation'], queue, consumers_connected, consumers_connected_min))

    def check_connection_conditions(self, options,host,port,DC):
        options["host"] = host
        options["port"] = port
        queue = options["queue"]
        url = "http://%s:%s/api/connections" % (options["host"], options["port"])
        self.log.info("URL for Connection Conditions--  \"{0}\"".format(url))
        data = self.send_request(DC, url, options)
        if data is None:
            return

        open_connections = len(data)

        open_connections_min = options["default_conditions"].get("open_connections")

        if open_connections is not None and open_connections < open_connections_min:
            self.send_notification(DC, options, "- <b>[ Alert - Node - %s ]</b> %s [ Condition: open_connections = %d < %d ]" % (options['rabbitServerLocation'],queue, open_connections, open_connections_min))

    def check_node_conditions(self, options,host,port,DC):
        options["host"] = host
        options["port"] = port
        queue = options["queue"]
        url = "http://%s:%s/api/nodes" % (options["host"], options["port"])
        self.log.info("URL for Node Conditions--  \"{0}\"".format(url))
        data = self.send_request(DC, url, options)
        if data is None:
            return

        nodes_running = len(data)

        conditions = options["default_conditions"]
        nodes_run = conditions.get("nodes_running")
        node_memory = conditions.get("node_memory_used")

        if nodes_run is not None and nodes_running < nodes_run:
            self.send_notification(DC, options, "- <b>[ Alert - Node - %s ]</b> %s [ Condition: nodes_running = %d < %d ]" % (options['rabbitServerLocation'],queue, nodes_running, nodes_run))

        for node in data:
            if node_memory is not None and node.get("mem_used") > (node_memory * 1000000):
                self.send_notification(DC, options, "- <b>[ Alert - Node - %s ]</b> %s [ Condition: node %s - node_memory_used = %d > %d MBs ]" % (options['rabbitServerLocation'],queue, node.get("name"), node.get("mem_used"), node_memory))

    def send_request(self, DC, url, options):
        queue = options["queue"]
        print("Printing options in send request")
        print(options)
        print("Printing options in send request")
        exchange = options["exchanges"]
        print("In send Request function_________________________")
        print(exchange)
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, url, options["username"], options["password"])
        handler = urllib2.HTTPBasicAuthHandler(password_mgr)
        opener = urllib2.build_opener(handler)

        try:
            request = opener.open(url)
            self.log.info("Response received after opening URL....")
            response = request.read()
            request.close()

            data = json.loads(response)
            self.log.info("Json data received....")
            return data
        except (urllib2.HTTPError) as e:
            if hasattr(e,'code') or hasattr(e,'reason'):
                if e.code == 404 :
                    print(e.code)
                    self.send_notification(DC, options, "- <b>[ CRITICAL - Queue - %s ] %s [ QUEUE NOT FOUND!!! Error Code - %s %s ]</b>" %(options['rabbitServerLocation'],queue,e.code,e.reason))
                if e.code == 408 :
                    self.send_notification(DC, options, "- <b>[ CRITICAL - Node - %s] %s [ SERVER NOT FOUND!!! %s ]</b>" %(options['rabbitServerLocation'],queue,e.reason))
        except (urllib2.URLError) as e:   
            self.send_notification(DC, options, "- <b>[ CRITICAL - Node - %s ] %s `` %s `` </b>" %(options['rabbitServerLocation'],queue,e))
            return None

    def send_notification(self, DC, options, body,tags=True):

        if options["host"] == "198.19.254.159" :
            print(options["host"]) 
            to_monitor_host = DC
            print(to_monitor_host)
            
        if options["host"] == "dcv-automation-amqp.svpod.dc-01.com" :
            print(options["host"])
            to_monitor_host = "RTP"
            print(to_monitor_host)
            
        if options["host"] == "dcv-automation-amqp.svpod.dc-02.com" :
            print(options["host"]) 
            to_monitor_host = "SNG"
            print(to_monitor_host)
            
        if options["host"] == "dcv-automation-amqp.svpod.dc-03.com" :
            print(options["host"]) 
            to_monitor_host = "LON"
            print(to_monitor_host)

        queue = options["queue"]
        queue_conditions = options["conditions"][queue]
        exchange = options["exchanges"]
        #exchange_conditions = options["exchangeconditions"][exchange]
        spark_room_id = queue_conditions.get("spark-room-id")
        print(spark_room_id)
        spark_bearer_id = queue_conditions.get("spark-bearer-id")
        print(spark_bearer_id)
        if spark_room_id is not None and spark_bearer_id is not None:
            spark_room_id = queue_conditions.get("spark-room-id")
            spark_bearer_id = queue_conditions.get("spark-bearer-id")
            print(spark_room_id)
            print(spark_bearer_id)
        else :
            spark_room_id = options["spark-room-id"]
            print(spark_room_id)
            spark_bearer_id = options["spark-bearer-id"]    
            print(spark_bearer_id)
        
        text_tag = " [RabbitMQ_Server_Location: %s] [Monitor_Location: %s]" % (to_monitor_host,os.environ['LOCATION'])
        text_spark = ""
        if tags == True:
            text_spark = "%s %s" % (body, text_tag)
        else:
            text_spark = "%s" % (body)
        print(text_spark)
        #text = "%s [Location: %s] [Monitor: %s]" % (body, DC, to_monitor_host)
        self.log.info("Text for send_notifications--  \"{0}\"".format(text_spark))
        spark_room_id = options["spark-room-id"]
        spark_bearer_id = options["spark-bearer-id"]
        self.log.info("Sending Spark notification: \"{0}\"".format(body))
        conn = httplib.HTTPSConnection("api.ciscospark.com")
        
        payload = "{\n\t\"roomId\": \"%s\",\n\t\"markdown\": \"%s\"\n}\n" % (spark_room_id, text_spark)
        headers = {
            'authorization': "Bearer "+spark_bearer_id,
            'content-type': "application/json",
            'cache-control': "no-cache",
            }
        conn.request("POST", "/v1/messages", payload, headers)
        res = conn.getresponse()
        data = res.read()
        
def monitorrabbit(host, port,DC,reports=False):

    print('DCDCDCDCDCDCDCDCDCDCDCDC is')
    print(DC) 
    print("HOSTHOSTHOSTHOST is")
    print(host)
  
    log = logger.Logger()
    rabbitmq_alert = RabbitMQAlert(log)

    #Initialize
    global jsonForInflux
    jsonForInflux=[]

    #######################
    # Options
    #######################
    opt_resolver = optionsresolver.OptionsResolver(log)
    #options = opt_resolver.setup_options()
    
    if DC == 'RTP' and host == '198.19.254.159' :
        options = opt_resolver.setup_options_RTP()
        options['rabbitServerLocation']=DC
    if DC == 'SNG' and host == '198.19.254.159' :
        options = opt_resolver.setup_options_SNG()
        options['rabbitServerLocation']=DC
    if DC == 'LON' and host == '198.19.254.159' :
        options = opt_resolver.setup_options_LON()
        options['rabbitServerLocation']=DC 

    if host == 'dcv-automation-amqp.svpod.dc-02.com' :
        options = opt_resolver.setup_options_SNG()
        options['rabbitServerLocation']="SNG"
    if host == 'dcv-automation-amqp.svpod.dc-03.com' :
        options = opt_resolver.setup_options_LON()
        options['rabbitServerLocation']="LON"
    if host == 'dcv-automation-amqp.svpod.dc-01.com' :
        options = opt_resolver.setup_options_RTP()
        options['rabbitServerLocation']="RTP"

    ####################
    # Queues
    ####################
    #while True:
    for queue in options["queues"]:
        options["queue"] = queue
        queue_conditions = options["conditions"][queue]
        log.info("Following are queue_conditions:")
        log.info(queue_conditions)

        if "ready_queue_size" in queue_conditions \
                or "unack_queue_size" in queue_conditions \
                or "total_queue_size" in queue_conditions \
                or "queue_consumers_connected_min" in queue_conditions \
                or "queue_consumers_connected_max" in queue_conditions \
                or "spark-room-id" in queue_conditions \
                or "spark-bearer-id" in queue_conditions :
            rabbitmq_alert.check_queue_conditions(options,host,port,DC)
            #rabbitmq_alert.createJsonForInflux(options,host,port,DC)
         
    ####################
    # Nodes
    ####################
    # common checks for all queues
    default_conditions = options["default_conditions"]
    if "nodes_running" in default_conditions:
        rabbitmq_alert.check_node_conditions(options,host,port,DC)
    if "open_connections" in default_conditions:
        rabbitmq_alert.check_connection_conditions(options,host,port,DC)
    if "consumers_connected" in default_conditions:
        rabbitmq_alert.check_consumer_conditions(options,host,port,DC)

    ####################
    # Exchanges
    ####################
    for exchange in options["exchanges"]:
        options["queue"] = queue
        options["exchanges"] = exchange
        exchange_conditions = options["exchangeconditions"][exchange]
        log.info("Following are exchange_conditions:")
        log.info(exchange_conditions)
        
        if "message_rate_in" in exchange_conditions \
                or "message_rate_out" in exchange_conditions \
                or "bindings" in exchange_conditions :
            rabbitmq_alert.get_data_for_exchanges(options, host, port, DC)


    ######################
    # Dashboard (influxDB)
    ######################
    rabbitmq_alert.send_notification(DC, options, "<b>[ Debug - Influx - %s ]</b>  [ Sending...  ]" % (options['rabbitServerLocation']))
    influx.writeToInfluxDb(jsonForInflux,credsFile='/root/creds/creds.cfg',influxDb='influxGlobal',ssl=True, verify_ssl=True)
    #rabbitmq_alert.send_notification(DC, options, "<b>[ Debug - Influx - %s ]</b>  [ JsonforInflux: %s ]" % (options['rabbitServerLocation'],jsonForInflux))

    ####################
    # Reports
    ####################
    if reports == True:
        CONFIG_FILE_PATHS = []
        CONFIG_FILE_PATHS = ['/root/rabbitmqalert/config_RTP.ini','/root/rabbitmqalert/config_SNG.ini','/root/rabbitmqalert/config_LON.ini']
        CONFIG_FILE_DC = ['RTP','LON','SNG']
        for eachfile,file_dc in zip(CONFIG_FILE_PATHS,CONFIG_FILE_DC):
            with open(eachfile) as f:
                content=f.readlines()
            output='RabbitMonitor in %s checking on server %s with config' %(DC,file_dc)
            print(output)
            for line in content:
                if "[Conditions:" in line:
                    output=output +  " <br/> Queue: " + re.sub('[\[\]]','', line.split(":")[1][:-1])
                if "ready_queue_size" in line:
                    output=output + " <br/> -  Ready Messages: " + line.split("=")[1][:-1]
                if "unack_queue_size" in line:
                    output=output + "<br/> -  UnAcked Messages: " + line.split("=")[1][:-1]
                if "queue_consumers_connected_min" in line:
                    output=output + "<br/> -  Consumers_min: " + line.split("=")[1][:-1]
                if "queue_consumers_connected_max" in line:
                    output=output + "<br/> -  Consumers_max: " + line.split("=")[1][:-1]
            rabbitmq_alert.send_notification(DC, options, "<b>[ Config Report - %s ]</b>  %s <br/>" % (file_dc,output),tags=False)

     

def main(): 
    log = logger.Logger()
    log.info("Starting application...")
    location=os.environ['LOCATION']
    log.info("Location recieved from controller!!")
    print(location)
    opt_resolver = optionsresolver.OptionsResolver(log)
    options = opt_resolver.setup_options_RTP()
    

    rabbitServers={
    "dcloud.test.sharedservices": {"dcv-automation-amqp.svpod.dc-01.com" : 24002,"dcv-automation-amqp.svpod.dc-02.com" : 24002, "dcv-automation-amqp.svpod.dc-03.com" : 24002},
    "dcloud.rtp.sharedservices": {"198.19.254.159" : 24002,"dcv-automation-amqp.svpod.dc-02.com" : 24002, "dcv-automation-amqp.svpod.dc-03.com" : 24002},
    "dcloud.sng.sharedservices": {"198.19.254.159" : 24002,"dcv-automation-amqp.svpod.dc-01.com" : 24002,"dcv-automation-amqp.svpod.dc-03.com" : 24002},
    "dcloud.lon.sharedservices": {"198.19.254.159" : 24002,"dcv-automation-amqp.svpod.dc-01.com" : 24002,"dcv-automation-amqp.svpod.dc-02.com" : 24002}
    }


    log.info("Location received: " + str(location))
    count = 1
    reportcount = 0
    while True:
        for rabbitServer, rabbitServerPort in rabbitServers[location].items():
            count = count+1
            reportcount = reportcount+1
            if reportcount >= 60:
                reports = True
                reportcount = 0
            else:
                reports = False
            monitorrabbit(rabbitServer, rabbitServerPort,location.split(".")[1].upper(),reports=reports)

        time.sleep(options["check_rate"])

   

if __name__ == "__main__":
    main()
