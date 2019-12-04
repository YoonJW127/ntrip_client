#!/usr/bin/python

import rospy
import socket

from base64 import b64encode
from rtcm_msgs.msg import Message

def rtcm_run():
    # Init ROS Node
    rospy.init_node('ntrip_client_node', anonymous=True)

    # Setting for NTRIP
    ntrip_server = rospy.get_param('~ntrip_server', 'ntrip.server.com')
    ntrip_mountpoint = rospy.get_param('~ntrip_mountpoint', 'mountpoint')
    ntrip_port = rospy.get_param('~ntrip_port', 2101)
    ntrip_user = rospy.get_param('~ntrip_user', 'user')
    ntrip_pass = rospy.get_param('~ntrip_pass', 'pass')
    ntrip_bufSize = rospy.get_param('~ntrip_bufSize', 1024)

    ntrip_stop = False

    # Make Publisher
    rtcm_pub = rospy.Publisher("rtcm_topic", Message, queue_size=1)

    # Make header for ntrip
    pwd = b64encode("{}:{}".format(ntrip_user, ntrip_pass))
    header = \
        "GET /{} HTTP/1.1\r\n".format(ntrip_mountpoint) +\
        "HOST: {}\r\n".format(ntrip_server) +\
        "Ntrip-Version: Ntrip/2.0\r\n" +\
        "User-Agent: NTRIP ntrip_ros\r\n" +\
        "Connection: close\r\n" +\
        "Authorization: Basic {}\r\n\r\n".format(pwd)

    try:
        # Open the socket for NTRIP
        ntrip = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #ntrip.settimeout(10)	# Set timeout
        ntrip.connect((ntrip_server, ntrip_port))
        ntrip.send(header)

        # Check the server connection
        resp = ntrip.recv(ntrip_bufSize)
        if ('200' in resp) and ('OK' in resp):
            rospy.loginfo("Server Connection")
        else:
            rospy.logerr("NTRIP: NOT WORKING")
            ntrip_stop = True
            ntrip.close()

        # TODO: The check to server status

        # Receive the RTCM data
        rtcm_msg = Message()
        while (not ntrip_stop) and (not rospy.is_shutdown()):
            buf = ""
            buf = ntrip.recv(ntrip_bufSize)

            rtcm_msg.message = buf
            rtcm_msg.header.seq += 1
            rtcm_msg.header.stamp = rospy.get_rostime()

            rtcm_pub.publish(rtcm_msg)

    except rospy.ROSInterruptException:
        ntrip.close()  # Close ntrip socket

if __name__ == '__main__':
    rtcm_run()
