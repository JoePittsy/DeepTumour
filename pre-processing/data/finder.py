import pickle
with open("train.txt", "r") as f:
	data = f.read()

data = [line[13:27] for line in data.split("\n")]

with open('training.pkl', 'wb') as f:
	pickle.dump(data, f)
print(data) 
