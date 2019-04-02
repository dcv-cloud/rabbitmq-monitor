#! /usr/bin/python2
# -*- coding: utf-8 -*-

import optparse
import ConfigParser
import os.path
import logger

#CONFIG_FILE_PATH = r"/root/rabbitmqalert/config.ini"


class OptionsResolver:
    def __init__(self, logger):
        self.log = logger

    def setup_options_RTP(self):
        CONFIG_FILE_PATH = r"/root/rabbitmqalert/config_RTP.ini"
        arguments = optparse.OptionParser()
        arguments.add_option("-c", "--config-file", dest="config_file", help="Path of the configuration file", type="string")
        #arguments.add_option("--host", dest="host", help="RabbitMQ API address", type="string")
        #arguments.add_option("--port", dest="port", help="RabbitMQ API port", type="string")
        arguments.add_option("--username", dest="username", help="RabbitMQ API username", type="string")
        arguments.add_option("--password", dest="password", help="RabbitMQ API password", type="string")
        arguments.add_option("--vhost", dest="vhost", help="Name of the vhost to inspect", type="string")
        arguments.add_option("--queues", dest="queues", help="List of comma-separated queue names to inspect", type="string")
        arguments.add_option("--check-rate", dest="check_rate", help="Conditions check frequency, in seconds.", type="int")

        arguments.add_option("--ready-queue-size", dest="ready_queue_size", help="Size of Ready messages on the queue to alert as warning", type="int")
        arguments.add_option("--unacknowledged-queue-size", dest="unack_queue_size", help="Size of the Unacknowledged messages on the queue to alert as warning", type="int")
        arguments.add_option("--total-queue-size", dest="total_queue_size", help="Size of the Total messages on the queue to alert as warning", type="int")
        arguments.add_option("--consumers-connected", dest="consumers_connected", help="The number of consumers that should be connected", type="int")
        #arguments.add_option("--queue-consumers-connected", dest="queue_consumers_connected",help="The number of consumers that should be checked",type="int")
        arguments.add_option("--queue-consumers-connected_min", dest="queue_consumers_connected_min",help="The number of consumers that should be less than the given value",type="int")
        arguments.add_option("--queue-consumers-connected_max", dest="queue_consumers_connected_max",help="The number of consumers that should be greater than the given value",type="int")
        arguments.add_option("--open-connections", dest="open_connections", help="The number of open connections", type="int")
        arguments.add_option("--nodes-running", dest="nodes_running", help="The number of nodes running", type="int")
        arguments.add_option("--node-memory-used", dest="node_memory_used", help="Memory used by each node in MBs", type="int")
        arguments.add_option("--publish-in",dest="message_rate_in",help="The size for messages published-in to alert as warning",type="int")
        arguments.add_option("--publish-out",dest="message_rate_out",help="The size for messages published-out to alert as warning",type="int")
        arguments.add_option("--bindings",dest="bindings",help="The size of bindings to alert as warning",type="int")
        arguments.add_option("--spark-bot-id", dest="spark_bot_id", help="Spark bot id", type="string")
        arguments.add_option("--spark-bearer-id", dest="spark_bearer-id", help="Spark bearer id", type="string")
        cli_arguments = arguments.parse_args()[0]

        # set as defaults the cli argument values
        config_file_options = ConfigParser.ConfigParser(vars(cli_arguments))

        options = dict()
        if os.path.isfile(CONFIG_FILE_PATH) and not cli_arguments.config_file:
            config_file_options.read(CONFIG_FILE_PATH)
            self.log.info("Using configuration file \"{0}\"".format(CONFIG_FILE_PATH))
        elif cli_arguments.config_file:
            self.log.info("Using configuration file \"{0}\"".format(cli_arguments.config_file))
            if not os.path.isfile(cli_arguments.config_file):
                self.log.error("The provided configuration file \"{0}\" does not exist".format(cli_arguments.config_file))
                exit(1)

            config_file_options.read(cli_arguments.config_file)
            
        options["username"] = cli_arguments.username or config_file_options.get("Server", "username")
        options["password"] = cli_arguments.password or config_file_options.get("Server", "password")
        options["vhost"] = cli_arguments.vhost or config_file_options.get("Server", "vhost")
        options["check_rate"] = cli_arguments.check_rate or config_file_options.getfloat("Server", "check_rate")
        options["spark-room-id"] = cli_arguments.check_rate or config_file_options.get("spark", "spark-room-id")
        options["spark-bearer-id"] = cli_arguments.check_rate or config_file_options.get("spark", "spark-bearer-id")
        options["queues"] = cli_arguments.queues or config_file_options.get("Server", "queues")
        options["exchanges"] = cli_arguments.check_rate or config_file_options.get("Server", "Exchanges")
        options["queues"] = options["queues"].split(",")
        options["exchanges"] = options["exchanges"].split(",")
        print("________________________________________________")
        print(options["exchanges"])
        print("__________________________________________________")
        # get queue specific condition values if any, else construct from the generic one
        conditions = OptionsResolver.construct_conditions(options, cli_arguments, config_file_options)
        exchangeconditions = OptionsResolver.construct_exchangeconditions(options, cli_arguments, config_file_options)
        options = dict(options.items() + conditions.items() + exchangeconditions.items())
        return options


    def setup_options_SNG(self):
        CONFIG_FILE_PATH = r"/root/rabbitmqalert/config_SNG.ini"
        arguments = optparse.OptionParser()
        arguments.add_option("-c", "--config-file", dest="config_file", help="Path of the configuration file", type="string")
        #arguments.add_option("--host", dest="host", help="RabbitMQ API address", type="string")
        #arguments.add_option("--port", dest="port", help="RabbitMQ API port", type="string")
        arguments.add_option("--username", dest="username", help="RabbitMQ API username", type="string")
        arguments.add_option("--password", dest="password", help="RabbitMQ API password", type="string")
        arguments.add_option("--vhost", dest="vhost", help="Name of the vhost to inspect", type="string")
        arguments.add_option("--queues", dest="queues", help="List of comma-separated queue names to inspect", type="string")
        arguments.add_option("--check-rate", dest="check_rate", help="Conditions check frequency, in seconds.", type="int")

        arguments.add_option("--ready-queue-size", dest="ready_queue_size", help="Size of Ready messages on the queue to alert as warning", type="int")
        arguments.add_option("--unacknowledged-queue-size", dest="unack_queue_size", help="Size of the Unacknowledged messages on the queue to alert as warning", type="int")
        arguments.add_option("--total-queue-size", dest="total_queue_size", help="Size of the Total messages on the queue to alert as warning", type="int")
        arguments.add_option("--consumers-connected", dest="consumers_connected", help="The number of consumers that should be connected", type="int")
        #arguments.add_option("--queue-consumers-connected", dest="queue_consumers_connected",help="The number of consumers that should be checked",type="int")
        arguments.add_option("--queue-consumers-connected_min", dest="queue_consumers_connected_min",help="The number of consumers that should be less than the given value",type="int")
        arguments.add_option("--queue-consumers-connected_max", dest="queue_consumers_connected_max",help="The number of consumers that should be greater than the given value",type="int")
        arguments.add_option("--open-connections", dest="open_connections", help="The number of open connections", type="int")
        arguments.add_option("--nodes-running", dest="nodes_running", help="The number of nodes running", type="int")
        arguments.add_option("--node-memory-used", dest="node_memory_used", help="Memory used by each node in MBs", type="int")
        arguments.add_option("--publish-in",dest="message_rate_in",help="The size for messages published-in to alert as warning",type="int")
        arguments.add_option("--publish-out",dest="message_rate_out",help="The size for messages published-out to alert as warning",type="int")
        arguments.add_option("--bindings",dest="bindings",help="The size of bindings to alert as warning",type="int")
        arguments.add_option("--spark-bot-id", dest="spark_bot_id", help="Spark bot id", type="string")
        arguments.add_option("--spark-bearer-id", dest="spark_bearer_id", help="Spark bearer id", type="string")
        cli_arguments = arguments.parse_args()[0]

        # set as defaults the cli argument values
        config_file_options = ConfigParser.ConfigParser(vars(cli_arguments))

        options = dict()
        if os.path.isfile(CONFIG_FILE_PATH) and not cli_arguments.config_file:
            config_file_options.read(CONFIG_FILE_PATH)
            self.log.info("Using configuration file \"{0}\"".format(CONFIG_FILE_PATH))
        elif cli_arguments.config_file:
            self.log.info("Using configuration file \"{0}\"".format(cli_arguments.config_file))
            if not os.path.isfile(cli_arguments.config_file):
                self.log.error("The provided configuration file \"{0}\" does not exist".format(cli_arguments.config_file))
                exit(1)

            config_file_options.read(cli_arguments.config_file)

        options["username"] = cli_arguments.username or config_file_options.get("Server", "username")
        options["password"] = cli_arguments.password or config_file_options.get("Server", "password")
        options["vhost"] = cli_arguments.vhost or config_file_options.get("Server", "vhost")
        options["check_rate"] = cli_arguments.check_rate or config_file_options.getfloat("Server", "check_rate")
        options["spark-room-id"] = cli_arguments.check_rate or config_file_options.get("spark", "spark-room-id")
        options["spark-bearer-id"] = cli_arguments.check_rate or config_file_options.get("spark", "spark-bearer-id")
        options["queues"] = cli_arguments.queues or config_file_options.get("Server", "queues")
        options["exchanges"] = cli_arguments.check_rate or config_file_options.get("Server", "Exchanges")
        options["queues"] = options["queues"].split(",")
        options["exchanges"] = options["exchanges"].split(",")

        # get queue specific condition values if any, else construct from the generic one
        conditions = OptionsResolver.construct_conditions(options, cli_arguments, config_file_options)
        exchangeconditions = OptionsResolver.construct_exchangeconditions(options, cli_arguments, config_file_options)
        options = dict(options.items() + conditions.items() + exchangeconditions.items())
        return options

    def setup_options_LON(self):
        CONFIG_FILE_PATH = r"/root/rabbitmqalert/config_LON.ini"
        arguments = optparse.OptionParser()
        arguments.add_option("-c", "--config-file", dest="config_file", help="Path of the configuration file", type="string")
        #arguments.add_option("--host", dest="host", help="RabbitMQ API address", type="string")
        #arguments.add_option("--port", dest="port", help="RabbitMQ API port", type="string")
        arguments.add_option("--username", dest="username", help="RabbitMQ API username", type="string")
        arguments.add_option("--password", dest="password", help="RabbitMQ API password", type="string")
        arguments.add_option("--vhost", dest="vhost", help="Name of the vhost to inspect", type="string")
        arguments.add_option("--queues", dest="queues", help="List of comma-separated queue names to inspect", type="string")
        arguments.add_option("--check-rate", dest="check_rate", help="Conditions check frequency, in seconds.", type="int")

        arguments.add_option("--ready-queue-size", dest="ready_queue_size", help="Size of Ready messages on the queue to alert as warning", type="int")
        arguments.add_option("--unacknowledged-queue-size", dest="unack_queue_size", help="Size of the Unacknowledged messages on the queue to alert as warning", type="int")
        arguments.add_option("--total-queue-size", dest="total_queue_size", help="Size of the Total messages on the queue to alert as warning", type="int")
        arguments.add_option("--consumers-connected", dest="consumers_connected", help="The number of consumers that should be connected", type="int")
        #arguments.add_option("--queue-consumers-connected", dest="queue_consumers_connected",help="The number of consumers that should be checked",type="int")
        arguments.add_option("--queue-consumers-connected_min", dest="queue_consumers_connected_min",help="The number of consumers that should be less than the given value",type="int")
        arguments.add_option("--queue-consumers-connected_max", dest="queue_consumers_connected_max",help="The number of consumers that should be greater than the given value",type="int")
        arguments.add_option("--open-connections", dest="open_connections", help="The number of open connections", type="int")
        arguments.add_option("--nodes-running", dest="nodes_running", help="The number of nodes running", type="int")
        arguments.add_option("--node-memory-used", dest="node_memory_used", help="Memory used by each node in MBs", type="int")
        arguments.add_option("--publish-in",dest="message_rate_in",help="The size for messages published-in to alert as warning",type="int")
        arguments.add_option("--publish-out",dest="message_rate_out",help="The size for messages published-out to alert as warning",type="int")
        arguments.add_option("--bindings",dest="bindings",help="The size of bindings to alert as warning",type="int")
        arguments.add_option("--spark-bot-id", dest="spark_bot_id", help="Spark bot id", type="string")
        arguments.add_option("--spark-bearer-id", dest="spark_bearer_id", help="Spark bearer id", type="string")
        cli_arguments = arguments.parse_args()[0]

        # set as defaults the cli argument values
        config_file_options = ConfigParser.ConfigParser(vars(cli_arguments))

        options = dict()
        if os.path.isfile(CONFIG_FILE_PATH) and not cli_arguments.config_file:
            config_file_options.read(CONFIG_FILE_PATH)
            self.log.info("Using configuration file \"{0}\"".format(CONFIG_FILE_PATH))
        elif cli_arguments.config_file:
            self.log.info("Using configuration file \"{0}\"".format(cli_arguments.config_file))
            if not os.path.isfile(cli_arguments.config_file):
                self.log.error("The provided configuration file \"{0}\" does not exist".format(cli_arguments.config_file))
                exit(1)

            config_file_options.read(cli_arguments.config_file)

        options["username"] = cli_arguments.username or config_file_options.get("Server", "username")
        options["password"] = cli_arguments.password or config_file_options.get("Server", "password")
        options["vhost"] = cli_arguments.vhost or config_file_options.get("Server", "vhost")
        options["check_rate"] = cli_arguments.check_rate or config_file_options.getfloat("Server", "check_rate")
        options["spark-room-id"] = cli_arguments.check_rate or config_file_options.get("spark", "spark-room-id")
        options["spark-bearer-id"] = cli_arguments.check_rate or config_file_options.get("spark", "spark-bearer-id")
        options["queues"] = cli_arguments.queues or config_file_options.get("Server", "queues")
        options["exchanges"] = cli_arguments.check_rate or config_file_options.get("Server", "Exchanges")
        options["queues"] = options["queues"].split(",")
        options["exchanges"] = options["exchanges"].split(",")

        # get queue specific condition values if any, else construct from the generic one
        conditions = OptionsResolver.construct_conditions(options, cli_arguments, config_file_options)
        exchangeconditions = OptionsResolver.construct_exchangeconditions(options, cli_arguments, config_file_options)
        options = dict(options.items() + conditions.items() + exchangeconditions.items())

        return options

    @staticmethod 
    def construct_int_option(cli_arguments, config_file_options, conditions, section_key, key, default_conditions=None):
        try:
            conditions[key] = getattr(cli_arguments, key) or config_file_options.getint(section_key, key)
        except:
            if default_conditions is not None and key in default_conditions:
                conditions[key] = default_conditions[key]
                
    @staticmethod 
    def construct_int_option_exchange(cli_arguments, config_file_options, exchangeconditions, section_key, key, default_conditions=None):
        try:
            exchangeconditions[key] = getattr(cli_arguments, key) or config_file_options.getint(section_key, key)
        except:
            if default_conditions is not None and key in default_conditions:
                exchangeconditions[key] = default_conditions[key]
                
    @staticmethod 
    def construct_str_option_exchange(cli_arguments, config_file_options, exchangeconditions, section_key, key, default_conditions=None):
        try:
            exchangeconditions[key] = getattr(cli_arguments, key) or config_file_options.get(section_key, key)
        except:
            if default_conditions is not None and key in default_conditions:
                exchangeconditions[key] = default_conditions[key]

    @staticmethod
    def construct_str_option(cli_arguments, config_file_options, conditions, section_key, key, default_conditions=None):
        try:
            conditions[key] = getattr(cli_arguments, key) or config_file_options.get(section_key, key)        
        except:
            if default_conditions is not None and key in default_conditions:
                conditions[key] = default_conditions[key]

    @staticmethod
    def construct_conditions(options, cli_arguments, config_file_options):
        conditions = dict()

        # get the generic condition values from the "[Conditions]" section
        default_conditions = dict()
        for key in ("ready_queue_size", "unack_queue_size", "total_queue_size", "consumers_connected",
                    "queue_consumers_connected_min", "queue_consumers_connected_max", "open_connections", "nodes_running", "node_memory_used"):
            OptionsResolver.construct_int_option(cli_arguments, config_file_options, default_conditions, "Conditions", key)
        for key in ("spark-room-id","spark-bearer-id"):   
            OptionsResolver.construct_str_option(cli_arguments, config_file_options, default_conditions, "Conditions", key)

        # check if queue specific condition sections exist, if not use the generic conditions
        if "queues" in options:
            for queue in options["queues"]:
                queue_conditions_section_name = "Conditions:" + queue
                queue_conditions = dict()
                conditions[queue] = queue_conditions
                print(conditions[queue])

                for key in ("ready_queue_size", "unack_queue_size", "total_queue_size", "queue_consumers_connected_min", "queue_consumers_connected_max","spark-room-id","spark-bearer-id"):
                    OptionsResolver.construct_int_option(cli_arguments, config_file_options, queue_conditions, queue_conditions_section_name, key, default_conditions)
                for key in ("spark-room-id","spark-bearer-id"):   
                    OptionsResolver.construct_str_option(cli_arguments, config_file_options, queue_conditions, queue_conditions_section_name, key, default_conditions)

        return {"conditions": conditions, "default_conditions": default_conditions}
    
    @staticmethod
    def construct_exchangeconditions(options, cli_arguments, config_file_options):
        exchangeconditions = dict()

        # get the generic condition values from the "[ExchangeConditions]" section
        default_conditions = dict()  
        for key in ("message_rate_in", "message_rate_out", "bindings"):
            OptionsResolver.construct_int_option_exchange(cli_arguments, config_file_options, default_conditions, "ExchangeConditions", key)
        for key in ("spark-room-id","spark-bearer-id"):   
            OptionsResolver.construct_str_option_exchange(cli_arguments, config_file_options, default_conditions, "ExchangeConditions", key)

        # check if queue specific ExchangeCondition sections exist, if not use the generic conditions
        if "exchanges" in options:
            for exchange in options["exchanges"]:
                exchange_conditions_section_name = "ExchangeConditions:" + exchange
                exchange_conditions = dict()
                exchangeconditions[exchange] = exchange_conditions
                for key in ("message_rate_in", "message_rate_out", "bindings"):
                    OptionsResolver.construct_int_option_exchange(cli_arguments, config_file_options, exchange_conditions, exchange_conditions_section_name, key, default_conditions)
                for key in ("spark-room-id","spark-bearer-id") :   
                    OptionsResolver.construct_str_option_exchange(cli_arguments, config_file_options, exchange_conditions, exchange_conditions_section_name, key, default_conditions)
                    
        return {"exchangeconditions": exchangeconditions, "default_conditions": default_conditions}
    
def main():
    log = logger.Logger()
    log.info("Starting application...")
    OR = OptionsResolver(log)
    options_RTP=OR.setup_options_RTP()
    options_SNG=OR.setup_options_SNG()
    options_LON=OR.setup_options_LON()
    print(options_RTP)
    print(options_SNG)
    print(options_LON)

if __name__ == "__main__":
    main()
