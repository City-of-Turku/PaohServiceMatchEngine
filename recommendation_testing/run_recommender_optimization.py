import argparse
import json
import requests
import optuna
from run_recommender_testing import run_recommendation_testing
from service_rec_test_cases import test_cases


def optimize_recommender(trial, language: str, recommender_to_optimize: str, top_k: int):
    ngram_min = trial.suggest_int("ngram_min", 0, 5, step=1)
    ngram_max = trial.suggest_int("ngram_max", ngram_min, 6, step=1)
    # bm25_k1 = trial.suggest_float("bm25_k1", 0.0, 2.0, step=0.1)
    # bm25_b = trial.suggest_float("bm25_b", 0.0, 1.0, step=0.1)
    # bm25_k1 = math.floor(bm25_k1*10)/10
    # bm25_b = math.floor(bm25_b*10)/10
    body = {
        "ngram_min": {"fi": ngram_min, "en": ngram_min, "sv": ngram_min},
        "ngram_max": {"fi": ngram_max, "en": ngram_max, "sv": ngram_max},
        "bm25_k1": 1.5,
        "bm25_b": 0.75
    }
    r = requests.post(
        'http://localhost:3001/createBM25', json=body)

    test_scores = run_recommendation_testing(
        test_cases, language=language, recommenders_to_test=[recommender_to_optimize], top_k=top_k, print_scores=False, plot_images=False)
    total_test_score = sum(
        map(lambda x: x[recommender_to_optimize], test_scores.values()))

    return total_test_score


def run_optimization(language: str, recommender_to_optimize: str, top_k: int, n_trials: int):
    study = optuna.create_study(direction="maximize")
    study.optimize(lambda trial: optimize_recommender(trial, language=language,
                   recommender_to_optimize=recommender_to_optimize, top_k=top_k), n_trials=n_trials)
    return study


def main():
    # Instantiate the parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", type=str, default="fi",
                        choices=["fi", "en", "sv"],
                        help="The language to optimize (fi, en, sv)")
    parser.add_argument("--recommender_to_optimize", type=str, default="all",
                        choices=["all", "lexical"],
                        help="Text recommender to optimize (all, lexical)")
    parser.add_argument("--top_k", type=int, default=15,
                        help="Top K recommendations used for optimization")
    parser.add_argument("--n_trials", type=int, default=30,
                        help="Number of trials used for optimization")
    parser.add_argument("--save_optimization_result", action="store_true",
                        help="Save optimization result to json file")
    args = parser.parse_args()

    print(
        f"Running {args.language} language optimization for recommender '{args.recommender_to_optimize}' with {args.n_trials} trials")

    study = run_optimization(
        language=args.language, recommender_to_optimize=args.recommender_to_optimize, top_k=args.top_k, n_trials=args.n_trials)

    print("============= OPTIMIZATION RESULTS =============")
    print(f"BEST TOTAL TEST SCORE: {study.best_value}")
    print(f"BEST PARAMS: {study.best_params}")

    if args.save_optimization_result:
        with open(f"{args.language}_optimization_result.json", "w", encoding="utf-8") as outfile:
            json.dump({"language": args.language, "optimized_params": study.best_params,
                      "best_total_test_score": study.best_value}, outfile, ensure_ascii=False)


if __name__ == "__main__":
    main()
