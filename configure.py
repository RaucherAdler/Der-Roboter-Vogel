from cryptography.fernet import Fernet
import os

if __name__ == "__main__":
    if (os.path.exists(".fernkey") and os.path.exists(".secrets")):
        res = input("Your keys are already saved, do you wish to rewrite them? (y/n):")
        if res[0] in ['n', 'N']:
            exit(0)

    fp = open(".fernkey", 'w')
    pkey = Fernet.generate_key()
    fp.write(pkey.decode())
    fp.close()
    print("Private key saved to '.fernkey', do not distribute with secrets.\n")

    fp = open(".secrets", 'w')
    fp.write(Fernet(pkey).encrypt(input("Enter your Discord token: ").encode()).decode())
    fp.write("\n")
    fp.write(Fernet(pkey).encrypt(input("Enter your MongoDB URI").encode()).decode())
    fp.close()
    print("Secrets encrypted and saved to '.secrets', do not distribute with private key.\n")
    exit(0)
