from sdnist.report.__main__ import run, setup

if __name__ == "__main__":
    input_cnf = setup()
    run(**input_cnf)
