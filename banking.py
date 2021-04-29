# Write your code here
import random
import functools
import sqlite3
from sqlite3 import Error


def main_menu():
    print("1. Create an account")
    print("2. Log into account")
    print("0. Exit")
    input_choice = int(input())
    return input_choice


def logged_in_menu():
    print("1. Balance")
    print("2. Add income")
    print("3. Do transfer")
    print("4. Close account")
    print("5. Log out")
    print("0. Exit")
    input_choice = int(input())
    return input_choice


def generate_account():
    return str(random.randrange(0, 999999999)).zfill(9)


def generate_card_no(account_no):
    check_sum = generate_check_sum('400000' + account_no)
    return '400000' + account_no + check_sum


def generate_check_sum(in_number):  # input a string
    # step 1. convert string to list of digits
    digits = [int(i) for i in in_number]
    # print(digits)

    # step 2. multiply odd digits by 2
    enumerated_digits = enumerate(digits, 1)
    multiplied_digits = [data*2 if index % 2 == 1 else data for index, data in enumerated_digits]
    # print(multiplied_digits)

    # step 3. subtract 9 form numbers over 9
    subtract_digits = [i - 9 if i > 9 else i for i in multiplied_digits]
    # print(subtract_digits)

    # step4. add all numbers
    sum_all_number = functools.reduce(lambda x, y: x + y, subtract_digits)
    # print(sum_all_number)

    # step5. find the check_sum
    if sum_all_number % 10 == 0:
        check_sum = 0
    else:
        check_sum = 10 - sum_all_number % 10
    # print(check_sum)

    return str(check_sum)


def verify_checksum(card_number):
    number = card_number[:-1]
    correct_checksum = generate_check_sum(number)
    return correct_checksum == card_number[-1]


def card_query(conn, card_number, pin):
    cur = conn.cursor()
    sql = ''' select * from card where number = ? and pin = ? '''
    cur.execute(sql, (card_number, pin))
    row = cur.fetchone()
    return row


def card_query_by_number(conn, card_number):
    cur = conn.cursor()
    sql = ''' select * from card where number = ?  '''
    cur.execute(sql, (card_number,))
    row = cur.fetchone()
    return row


def balance_query(conn, card_num, pin):
    cur = conn.cursor()
    sql = ''' select balance from card where number = ? and pin = ? '''
    cur.execute(sql, (card_num, pin))
    bal = cur.fetchone()[0]
    return bal


def transfer_money(conn, from_card_no, to_card_no, amount):
    cur = conn.cursor()
    sql_from_card = ''' update card set balance = balance - ? where number = ? '''
    sql_to_card = ''' update card set balance = balance + ? where number = ? '''
    cur.execute(sql_from_card, (amount, from_card_no))
    cur.execute(sql_to_card, (amount, to_card_no))
    conn.commit()


def delete_account(conn, card_number):
    cur = conn.cursor()
    sql_delete = ''' delete from card where number = ? '''
    cur.execute(sql_delete, (card_number,))
    conn.commit()


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    return conn


def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)


def insert_data(conn, data):
    """
    Insert new data into the card table
    :param conn:
    :param data:
    :return: card id
    """
    sql = ''' INSERT INTO card(number,pin)
              VALUES(?,?) '''
    cur = conn.cursor()
    cur.execute(sql, data)
    conn.commit()
    return cur.lastrowid


def add_income(conn, card_num, income):
    """
    Add income to a card
    :param conn: Connection object
    :param card_num:
    :param income: Amount to be added
    """
    sql = ''' Update card set balance = balance + ? 
              where number = ?
              '''
    cur = conn.cursor()
    cur.execute(sql, (income, card_num))
    conn.commit()


class Card:
    def __init__(self, card_number):
        self.balance = 0
        self.card_no = card_number
        self.pin = str(random.randint(0, 9999)).zfill(4)


if __name__ == '__main__':
    sql_create_card_table = """ CREATE TABLE IF NOT EXISTS card (
                                        id integer PRIMARY KEY,
                                        number text NOT NULL,
                                        pin text,
                                        balance integer default 0
                                    ); """
    connection = create_connection('card.s3db')
    with connection:
        create_table(connection, sql_create_card_table)
    while True:
        user_choice = main_menu()
        if user_choice == 1:  # Create an account
            acct_no = generate_account()
            card_no = generate_card_no(acct_no)
            your_card = Card(card_no)
            print("Your card has been created")
            print("Your card number:")
            print(your_card.card_no)
            print("Your card PIN:")
            print(your_card.pin)

            # insert data to card table
            with connection:
                insert_data(connection, (your_card.card_no, your_card.pin))

        elif user_choice == 2:  # Log into account
            in_card_no = input("Enter your card number:\n")
            in_pin = input("Enter you PIN:\n")
            # check if card exist in the system
            with connection:
                query_card = card_query(connection, in_card_no, in_pin)
                if query_card is not None:
                    print("You have successfully logged in!\n")
                    while True:
                        user_choice_logged_in = logged_in_menu()
                        if user_choice_logged_in == 1:  # Check balance
                            with connection:
                                balance = balance_query(connection, in_card_no, in_pin)
                                print(f"Balance: {balance}\n")
                                continue
                        elif user_choice_logged_in == 2:  # Add income
                            income_to_add = input("Enter income:\n")
                            with connection:
                                add_income(connection, in_card_no, income_to_add)
                            print("Income was added!\n")
                            continue
                        elif user_choice_logged_in == 3:  # Do transfer
                            print("Transfer")
                            card_no_destination = input("Enter card number:\n")
                            # check if transfer money to same account
                            if in_card_no == card_no_destination:
                                print("You can't transfer money to the same account!\n")
                                continue

                            # check if card number pass the Luhn algorithm
                            if not verify_checksum(card_no_destination):
                                print("Probably you made a mistake in the card number. Please try again!\n")
                                continue

                            with connection:
                                # check if card_no_destination exist in system
                                destination_card_query = card_query_by_number(connection, card_no_destination)
                                if destination_card_query is None:
                                    print("Such a card does not exist.\n")
                                    continue
                                transfer_amount = int(input("Enter how much money you want to transfer:\n"))
                                balance_tran = balance_query(connection, in_card_no, in_pin)
                                if balance_tran < transfer_amount:
                                    print("Not enough money!\n")
                                    continue
                                transfer_money(connection, in_card_no, card_no_destination, transfer_amount)
                                print("Success!\n")
                                continue
                        elif user_choice_logged_in == 4:  # Close account
                            with connection:
                                delete_account(connection, in_card_no)
                                print("The account has been closed!\n")
                                break
                        elif user_choice_logged_in == 5:  # Logout
                            break
                        elif user_choice_logged_in == 0:  # Exit
                            quit(0)
                        else:
                            print("Wrong choice")
                else:
                    print("Wrong card number or PIN!\n")
                    continue

        elif user_choice == 0:  # Exit
            print("Bye!")
            break
        else:
            print("Wrong choice\n")
