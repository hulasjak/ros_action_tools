#! /usr/bin/env python3

from datetime import datetime
import rospy
from std_msgs.msg import String
from actionlib_msgs.msg import GoalStatusArray
from ros_action_tools.msg import ActionAnalytics

actions_list = []
number_of_calls = []
mean_duration_list = []
total_duration_list = []
max_duration_list = []
started_list = []
start_time = []


def actions_callback(data, num):
    if len(data.status_list) > 0:
        if data.status_list[-1].status == 1 and not started_list[num]:
            start_time[num] = datetime.now()
            started_list[num] = True

        elif data.status_list[-1].status == 3 and started_list[num]:
            started_list[num] = False
            number_of_calls[num] += 1
            duration = (datetime.now() - start_time[num]).total_seconds()
            total_duration_list[num] += duration
            mean_duration_list[
                num] = total_duration_list[num] / number_of_calls[num]
            if duration > max_duration_list[num]:
                max_duration_list[num] = duration

        elif data.status_list[-1].status == 4 and started_list[num]:
            started_list[num] = False
            #can collect errors here


def start_sub_and_pub(action):
    #create new index for action
    actions_list.append(action)
    number_of_calls.append(0)
    mean_duration_list.append(0)
    total_duration_list.append(0)
    max_duration_list.append(0)
    started_list.append(False)
    start_time.append(0)
    #TODO move all the arrays to a class
    rospy.Subscriber(action,
                     GoalStatusArray,
                     actions_callback,
                     callback_args=len(actions_list) - 1)
    return rospy.Publisher('/action_analytics' + action.replace('/status', ''),
                           ActionAnalytics,
                           queue_size=10)


def get_all_actions():
    all_topics = rospy.get_published_topics()
    availible_actions = []
    for topic in all_topics:
        if '/status' in topic[0]:
            availible_actions.append(topic[0])

    return availible_actions


def main_publisher():
    rospy.init_node('action_anaylticss', anonymous=True)
    cached_set = set()
    publishers = []
    rate = rospy.Rate(10)  # 10hz
    while not rospy.is_shutdown():
        actions = set(get_all_actions())
        not_started_actions = list(actions.difference(cached_set))
        for action in not_started_actions:
            publishers.append(start_sub_and_pub(action))
            cached_set.add(action)

        for i, publisher in enumerate(publishers):
            msg = ActionAnalytics()
            msg.action_name = actions_list[i]
            msg.num_of_calls = number_of_calls[i]
            msg.mean_duration = mean_duration_list[i]
            msg.max_duration = max_duration_list[i]
            publisher.publish(msg)

        not_started_actions = []
        rate.sleep()


if __name__ == '__main__':
    try:
        main_publisher()
    except rospy.ROSInterruptException:
        pass