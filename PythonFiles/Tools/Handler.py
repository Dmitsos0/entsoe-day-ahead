

def gather():
    from PythonFiles.EnexGas.GetData import get_all_enex_gas
    from PythonFiles.entsoe.GetData import get_all_entsoe
    print("Making requests please do not close the program it may take a while")
    get_all_enex_gas()
    get_all_entsoe()
    print("Done collecting data!")

def train():
    from Models.light.main import train_model
    print("Training model!")
    train_model()
    print("Done training!")

def predict():
    from Models.light.main import test_model
    print("Making predictions")
    test_model()

def gather_and_train():
    gather()
    train()

def train_and_predict():
    train()
    predict()

def do_all():
    gather()
    train()
    predict()

