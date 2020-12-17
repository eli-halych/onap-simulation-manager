from steps import SimInstanceStep

sim = SimInstanceStep(cleanup=True, conf_name='pnf_simulator.yaml')
sim.execute()
sim.cleanup()