'''
Configure a brand new Cisco switch and generate a config file with output of desired show commands
'''

import serial
import sys
import time

import credentials
import confirmation_commands



READ_TIMEOUT = 8


def read_serial(console):
    '''
    Check if there is data waiting to be read
    Read and return it.
    else return null string
    '''
    data_bytes = console.inWaiting()
    if data_bytes:
        return console.read(data_bytes)
    else:
        return ""


def check_logged_in(console):
    '''
    Check if logged in to switch
    '''
    console.write("\r\n\r\n")
    time.sleep(1)
    prompt = read_serial(console)
    if '>' in prompt or '#' in prompt:
        return True
    else:
        return False


def login(console):
    '''
    Login to switch
    '''
    login_status = check_logged_in(console)
    if login_status:
        print "Already logged in"
        return None

    print "Logging into switch"
    while True:
        console.write("\r\n")
        time.sleep(1)

        input_data = read_serial(console)
        if not 'Username' in input_data:
            continue
        console.write(credentials.username + "\r\n")
        time.sleep(1)


        input_data = read_serial(console)
        if not 'Password' in input_data:
            continue
        console.write(credentials.password + "\r\n")
        time.sleep(1)



        login_status = check_logged_in(console)
        print read_serial(console)
        if login_status:
            print "We are logged in\n"
            break


def logout(console):
    '''
    Exit from console session
    '''
    print "Logging out from switch"
    while check_logged_in(console):
        console.write("exit\r\n")
        time.sleep(.5)

    print "Successfully logged out from switch"


def send_command(console, cmd=''):
    '''
    Send a command down the channel
    Return the output
    '''
    console.write(cmd + '\r\n')
    time.sleep(0.50)
    return read_serial(console)

def send_command_slow(console, cmd=''):
    '''
    Send a command down the channel with longer time to read the output
    Return the output
    '''
    console.write(cmd + '\r\n')
    time.sleep(2)
    return read_serial(console)    


def main():
    '''
    Testing using Python to interact to Cisco switch via serial port
    '''

    '''
    Get COM port from user
    '''
    com_port = 'COM' + raw_input('What is your COM port? > ')


    '''
    Get switch information from user and define variables
    '''

#    switch_mod = raw_input('What model switch are you configuring? > ')
    port_count = 'switchconfig' + raw_input('How many ports are on your switch? > ') + 'p.txt'
    ccm_id = raw_input('What is the CCM ID, including the site number? > ').upper()
    switch_num = raw_input('What is the switch number? > ')
    mgmt_ip = '172.31.31.' + str(255 - int(switch_num))
    hostname = 'hostname ' + ccm_id + '-swi0' + switch_num + '-c2960'
    print hostname
    print mgmt_ip


    print "\nInitializing serial connection"

    console = serial.Serial(
        port=com_port,
        baudrate=9600,
        parity="N",
        stopbits=1,
        bytesize=8,
        timeout=READ_TIMEOUT
    )


    print "\nChanging baudrate to 115200 for quicker configurationxxx"
    login(console)
    send_command(console, cmd='enable')
    send_command(console, cmd='terminal speed 115200')
    console.close()
    

    console = serial.Serial(
        port=com_port,
        baudrate=115200,
        parity="N",
        stopbits=1,
        bytesize=8,
        timeout=None
    )


    if not console.isOpen():
        sys.exit()

    with open(port_count) as f:
        content = f.readlines()
    content = [x.strip() for x in content] 

    print "\nRe-initializing serial connection"
    login(console)
    send_command(console, cmd='enable')
    

    '''
    Configure Device with specified config file
    '''
    print "\nConfiguring Device..."
    send_command(console, cmd='config terminal')
    send_command(console, cmd=hostname)
    send_command(console, cmd='interface Vlan2')
    send_command(console, cmd='ip address ' + mgmt_ip + ' 255.255.255.0')
    for line in content:
        send_command(console,cmd=line)  
    send_command(console, cmd='end')


    '''
    Generate config file with outputs
    '''
    print "\nGenerating Configuration File..."

    send_command(console, cmd='terminal length 0')
    with open(ccm_id + "-swi0" + switch_num + ".txt", "a+") as f:
        for e in confirmation_commands.conf_commands2:
            f.write(send_command_slow(console, cmd=e))

        for i in confirmation_commands.conf_commands:
            f.write(send_command(console, cmd=i))


    '''
    Revert to old terminal settings and logout
    '''
    print "\nReverting Terminal settings..."
    send_command(console, cmd='terminal length 24')
    send_command(console, cmd='terminal speed 9600')
    logout(console)
    console.close()


if __name__ == "__main__":
    main()