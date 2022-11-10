import random
import matplotlib.pyplot as plt

pick_prob = 0.6
sample_size = 100
runs = 1000
run_probs = []

for run in range(runs):
    sample_set = []
    for sample in range(sample_size):
        pickable_parts = sum(random.choices([1, 0], [pick_prob, 1 - pick_prob], k=5))
        sample_set.append(pickable_parts)

    run_probs.append(100 - (sample_set.count(0) / sample_size * 100))

print('Mean:', sum(run_probs) / len(run_probs))
plt.hist(run_probs)
plt.show()
