import copy
import random
import time

from evaluation import (decode_state, evaluate_state, generate_random_state,
                        move_vehicle, rotate_vehicle, swap_vehicles)

GA_CONTROL_POPULATION = 50
GA_ITERATION_VARIATIONS = [100, 300, 600]
GA_CONTROL_ITERATION = 300
GA_POPULATION_VARIATIONS = [20, 50, 100]
GA_MUTATION_RATE = 0.1

def initialize_population(population_size, vehicles, ship):
    population = []

    for i in range(population_size):
        state = generate_random_state(vehicles, ship)
        population.append(state)

    return population


def evaluate_population(population, vehicles, ship):
    evaluations = []
    for individual in (population):
        evaluate = evaluate_state(individual, vehicles, ship)
        evaluations.append(evaluate)

    return evaluations


def roulette_selection(population, fitness_scores):
    min_fitness = min(fitness_scores)
    portions = []
    for f in (fitness_scores):
        portion = f - min_fitness + 1
        portions.append(portion)
        
    return random.choices(population, weights=portions)[0]


def crossover(x, y):
    cut_point = random.randint(1, len(x))
    child = x[:cut_point] + y[cut_point:]

    return copy.deepcopy(child)


def mutation(child, vehicles, ship):
    mutating_vehicle = random.randint(1, len(child))
    mutate = random.choices(['swap','rotate','move'])
    if mutate == 'swap':
        j = random.choices([k for k in (len(child)) if k != mutating_vehicle])
        swap_vehicles(child, mutating_vehicle, j, vehicles, ship)
    elif mutate == 'rotate':
        rotate_vehicle(child, mutating_vehicle, vehicles, ship)
    else:
        move_vehicle(child, mutating_vehicle, vehicles, ship)
    return child


def genetic_algorithm(vehicles, ship, population_size=GA_CONTROL_POPULATION, max_iteration=GA_CONTROL_ITERATION, mutation_rate=GA_MUTATION_RATE):
    start_time = time.perf_counter()

    population = initialize_population(population_size, vehicles, ship)
    fitness_scores = evaluate_population(population, vehicles, ship)

    initial_fitness = max(fitness_scores)
    i = fitness_scores.index(initial_fitness)
    initial_state = copy.deepcopy(population[i])

    max_fitness_list = [max(fitness_scores)]
    avg_fitness_list = [sum(fitness_scores) / len(fitness_scores)]

    for i in range(max_iteration):
        new_population = []
        for j in range(population_size):
            x = roulette_selection(population, fitness_scores)
            y = roulette_selection(population, fitness_scores)
            child = crossover(x,y)
            if random.random() < mutation_rate:
                mutation(child, vehicles, ship)
            new_population.append(child)
        
        population = new_population

        fitness_scores = evaluate_population(population, vehicles, ship)
        max_fitness_list.append(max(fitness_scores))
        avg_fitness_list.append(sum(fitness_scores) / len(fitness_scores))

    duration = time.perf_counter() - start_time

    best_fitness_scores = max(fitness_scores)
    best_index = fitness_scores.index(best_fitness_scores)
    best_individual = population[best_index]

    return {
        "initial_state": decode_state(initial_state, vehicles),
        "initial_fitness": initial_fitness,
        "final_state": decode_state(best_individual, vehicles),
        "final_fitness": best_fitness_scores,
        "fitness_list": max_fitness_list,
        "duration": duration,
  
        "avg_fitness_list": avg_fitness_list,
        "population_size": population_size,
        "max_iteration": max_iteration,
    }