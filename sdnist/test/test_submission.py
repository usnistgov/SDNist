import sdnist.challenge.subsample


def test_subsample_census():
    generator = sdnist.challenge.subsample.SubsampleModel()
    sdnist.run(generator, challenge="census", override_results=True)
    sdnist.run(generator, challenge="census")

def test_subsample_taxi():
    generator = sdnist.challenge.subsample.SubsampleModel()
    sdnist.run(generator, challenge="taxi", override_results=True)
    sdnist.run(generator, challenge="taxi")


if __name__ == "__main__":
    test_subsample_taxi()