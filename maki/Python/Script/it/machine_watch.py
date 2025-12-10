import time
import socket
import smtplib
from email.mime.text import MIMEText

'''
check if machine (ip, port) is down
'''

ips = ['xxxx.yy.zz']
port = 135 #RPC, Distributed File System Namespaces

def main():
    for ip in ips:
        if host_is_down(ip, port):
            send_email(f'From machine {socket.gethostname()}', f'{ip}:{port} is down')
        else:
            print(f'{ip}:{port} is OK')

def host_is_down(ip, port):
    for i in range(retry):
        if port_is_open(ip, port):
            return False
        else:
            time.sleep(delay)
    return True

def port_is_open(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((ip, port))
        s.shutdown(socket.SHUT_RDWR)
        return True
    except:
        return False
    finally:
        s.close()

def send_email(subject, str_msg, joinlines = False):
    email_from = 'email.fr@email.com'
    email_to = 'email.to@email.com' #;email.bak@email.com'
    #create a text/plain message
    msg = MIMEText('\n'.join(str_msg) if joinlines else str_msg)
    msg['Subject'] = subject
    msg['From'] = email_from
    msg['To'] = email_to

    #send the message via our own SMTP server, but don't include the envelope header
    s = smtplib.SMTP('mail.yy.zz')
    s.sendmail(email_from, [email_to], msg.as_string())
    s.quit()

retry = 2
delay = 5
timeout = 3

if __name__ == '__main__':
    main()
