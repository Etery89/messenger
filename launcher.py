import subprocess


def run_launcher():

    processes = []

    while True:
        user_action = input('Пожалуйста выберите команду: quit - выход, start - запустить сервер и клиенты, \
                            close - закрыть все окна: ')

        if user_action == 'quit':
            break
        elif user_action == 'start':
            count_clients = int(input('Пожалуйста введите количество клиентов для запуска: '))
            client_names = []
            for num_client in range(count_clients):
                client_names.append(input(f'Пожалуйста введите имя клиента {num_client + 1}: '))
            processes.append(subprocess.Popen('gnome-terminal -- python3 run_server.py', shell=True))
            for num_client in range(len(client_names)):
                processes.append(subprocess.Popen(f'gnome-terminal -- python3 client.py --name {client_names[num_client]}', shell=True))
            # print(processes)
        elif user_action == 'close':
            while processes:
                process_for_delete = processes.pop()
                process_for_delete.kill()
                process_for_delete.terminate()


if __name__ == "__main__":
    run_launcher()