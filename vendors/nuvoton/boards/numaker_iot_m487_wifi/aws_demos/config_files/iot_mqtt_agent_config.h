/*
 * FreeRTOS V1.4.8
 * Copyright (C) 2020 Amazon.com, Inc. or its affiliates.  All Rights Reserved.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy of
 * this software and associated documentation files (the "Software"), to deal in
 * the Software without restriction, including without limitation the rights to
 * use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
 * the Software, and to permit persons to whom the Software is furnished to do so,
 * subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software. If you wish to use our Amazon
 * FreeRTOS name, please do so in a fair use way that does not cause confusion.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
 * FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
 * COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
 * IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 * CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 *
 * http://aws.amazon.com/freertos
 * http://www.FreeRTOS.org
 */

/**
 * @file iot_mqtt_agent_config.h
 * @brief MQTT agent config options.
 */

#ifndef _AWS_MQTT_AGENT_CONFIG_H_
#define _AWS_MQTT_AGENT_CONFIG_H_

#include "FreeRTOS.h"
#include "task.h"
#include "kconfig.h"
/**
 * @brief Controls whether or not to report usage metrics to the
 * AWS IoT broker.
 *
 * If mqttconfigENABLE_METRICS is set to 1, a string containing
 * metric information will be included in the "username" field of
 * the MQTT connect messages.
 */
#if defined( CONFIG_MQTT_ENABLE_METRICS )
    #define mqttconfigENABLE_METRICS                1
#else
    #define mqttconfigENABLE_METRICS                0
#endif

/**
 * @defgroup Metrics The metrics reported to the AWS IoT broker.
 *
 * If mqttconfigENABLE_METRICS is set to 1, these will be included
 * in the "username" field of MQTT connect messages.
 */
/** @{ */
#define mqttconfigMETRIC_SDK         "SDK=AmazonFreeRTOS"               /**< The SDK used by this device. */
#define mqttconfigMETRIC_VERSION     "Version="tskKERNEL_VERSION_NUMBER /**< The version number of this SDK. */
#define mqttconfigMETRIC_PLATFORM    "Platform=NumakerPFMM487"           /**< The platform that this SDK is running on. */
/** @} */

/**
 * @brief The maximum time interval in seconds allowed to elapse between 2 consecutive
 * control packets.
 */
#define mqttconfigKEEP_ALIVE_INTERVAL_SECONDS         ( CONFIG_MQTT_KEEP_ALIVE_INTERVAL_SECONDS )

/**
 * @brief Defines the frequency at which the client should send Keep Alive messages.
 *
 * Even though the maximum time allowed between 2 consecutive control packets
 * is defined by the mqttconfigKEEP_ALIVE_INTERVAL_SECONDS macro, the user
 * can and should send Keep Alive messages at a slightly faster rate to ensure
 * that the connection is not closed by the server because of network delays.
 * This macro defines the interval of inactivity after which a keep alive messages
 * is sent.
 */
#define mqttconfigKEEP_ALIVE_ACTUAL_INTERVAL_TICKS    ( pdMS_TO_TICKS(CONFIG_MQTT_KEEP_ALIVE_ACTUAL_INTERVAL_TICKS) )

/**
 * @brief The maximum interval in ticks to wait for PINGRESP.
 *
 * If PINGRESP is not received within this much time after sending PINGREQ,
 * the client assumes that the PINGREQ timed out.
 */
#define mqttconfigKEEP_ALIVE_TIMEOUT_TICKS            ( CONFIG_MQTT_KEEP_ALIVE_TIMEOUT_TICKS )

/**
 * @brief The maximum time in ticks for which the MQTT task is permitted to block.
 *
 * The MQTT task blocks until the user initiates any action or until it receives
 * any data from the broker. This macro controls the maximum time the MQTT task can
 * block. It should be set to a low number for the platforms which do not have any
 * mechanism to wake up the MQTT task whenever data is received on a connected socket.
 * This ensures that the MQTT task keeps waking up frequently and processes the
 * publish messages received from the broker, if any.
 */
#define mqttconfigMQTT_TASK_MAX_BLOCK_TICKS           ( CONFIG_MQTT_TASK_MAX_BLOCK_TICKS )

/**
 * @defgroup MQTTTask MQTT task configuration parameters.
 */
/** @{ */

#if defined( CONFIG_MQTT_TASK_STACK_DEPTH_DEPENDS_ON_STACK_SIZE )
    #define mqttconfigMQTT_TASK_STACK_DEPTH    ( configMINIMAL_STACK_SIZE * CONFIG_MQTT_TASK_STACK_DEPTH_MULTIPLIER )
#else
    #define mqttconfigMQTT_TASK_STACK_DEPTH ( CONFIG_MQTT_TASK_STACK_DEPTH )
#endif

#if defined( CONFIG_MQTT_TASK_PRIORITY_DEPENDS_ON_MAX_PRIORITY )
    #define mqttconfigMQTT_TASK_PRIORITY    ( configMAX_PRIORITIES - CONFIG_MQTT_TASK_PRIORITY_DIFFERENCE )
#else
    #define mqttconfigMQTT_TASK_PRIORITY ( tskIDLE_PRIORITY + CONFIG_MQTT_TASK_PRIORITY )
#endif

/** @} */

/**
 * @brief Maximum number of MQTT clients that can exist simultaneously.
 */
#define mqttconfigMAX_BROKERS            ( CONFIG_MQTT_MAX_BROKERS )

/**
 * @brief Maximum number of parallel operations per client.
 */
#define mqttconfigMAX_PARALLEL_OPS       ( CONFIG_MQTT_MAX_PARALLEL_OPS )

/**
 * @brief Time in milliseconds after which the TCP send operation should timeout.
 */
#define mqttconfigTCP_SEND_TIMEOUT_MS    ( CONFIG_MQTT_TCP_SEND_TIMEOUT_MS )

/**
 * @brief Length of the buffer used to receive data.
 */
#define mqttconfigRX_BUFFER_SIZE         ( CONFIG_MQTT_RX_BUFFER_SIZE )

#endif /* _AWS_MQTT_AGENT_CONFIG_H_ */
