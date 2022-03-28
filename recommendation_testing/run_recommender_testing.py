import argparse
import json
import requests
import matplotlib.pyplot as plt
from sklearn.metrics import auc
from service_rec_test_cases import test_cases


def recommend_services(text: str, text_recommender: str, language: str, top_k: int):
    body = {'need_text': text, 'top_k': top_k,   "municipalities": [], "life_events": [], "service_classes": [], "score_threshold": 0.0,
            "text_recommender": text_recommender, 'language': language}
    r = requests.post(
        'http://localhost/services/recommend', json=body)

    services = r.json()
    return(services)


def get_matched_services(response: list, test_cases: dict) -> list:
    matched_services = []
    for index, resp in enumerate(response):
        if next((item for item in test_cases if item["id"] == resp["id"]), None):
            matched_services.append(
                matched_services[index-1] + 1 if index > 0 else 1)
        else:
            matched_services.append(
                matched_services[index-1] if index > 0 else 0)
    matched_services.insert(0, 0)
    return matched_services


def run_recommendation_testing(test_cases: dict, language: str, recommenders_to_test: list = ['all', 'nlp', 'lexical'], top_k: int = 15, print_scores: bool = True, plot_images: bool = False) -> dict:
    test_scores = {}
    for test_case in test_cases:
        matches = {}
        for text_recommender in recommenders_to_test:
            response = recommend_services(
                test_cases.get(test_case).get('need_text').get(language), text_recommender=text_recommender, language=language, top_k=top_k)
            response = [{"name": resp["service"]["name"]["fi"], "score": resp["score"],
                        "id": resp["service"]["id"]} for resp in response]

            matches[text_recommender] = get_matched_services(
                response, test_cases.get(test_case).get('services'))

        theor_max_y = list(range(len(test_cases.get(test_case).get('services')) + 1)) + [len(
            test_cases.get(test_case).get('services'))] * (len(matches[recommenders_to_test[0]]) - len(test_cases.get(test_case).get('services')) - 1)
        theor_max_y = theor_max_y[:top_k + 1]

        if plot_images:
            for text_recommender in recommenders_to_test:
                plt.plot(list(range(len(matches[text_recommender]))),
                         matches[text_recommender], label=text_recommender)

            plt.plot(list(range(len(matches[recommenders_to_test[0]]))),
                     theor_max_y, label='Theor. max')
            plt.legend()
            plt.title(test_cases.get(test_case).get('need_text').get(language))
            plt.locator_params(axis="both", integer=True)
            plt.xlabel('Num recommendations')
            plt.ylabel('Num matches')
            plt.show()

        scores = {}
        score_max = auc(
            list(range(len(matches[recommenders_to_test[0]]))), theor_max_y)
        for text_recommender in recommenders_to_test:
            scores[text_recommender] = auc(list(
                range(len(matches[text_recommender]))), matches[text_recommender]) / score_max
        test_scores[test_cases.get(test_case).get(
            'need_text').get(language)] = scores

        if print_scores:
            print(test_cases.get(test_case).get('need_text').get(language))
            print(scores)
            print('======================================================')

    return test_scores


def main():
    # Instantiate the parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", type=str, default='fi',
                        choices=["fi", "en", "sv"],
                        help="The language to test (fi, en, sv)")
    parser.add_argument("--recommenders_to_test", nargs="+", default=[
                        'all', 'nlp', 'lexical'], help="List of text recommenders to test (all, nlp, lexical)")
    parser.add_argument("--top_k", type=int, default=15,
                        help="Top K recommendations used for testing")
    parser.add_argument("--plot_images", action="store_true",
                        help="Plot test case visualizations")
    parser.add_argument("--save_test_scores", action="store_true",
                        help="Save test scores to json file")
    args = parser.parse_args()

    print(
        f"Running {args.language} language tests using {args.recommenders_to_test} recommenders with top_k={args.top_k} and plot_images={args.plot_images}")

    test_scores = run_recommendation_testing(
        test_cases, language=args.language, recommenders_to_test=args.recommenders_to_test, top_k=args.top_k, plot_images=args.plot_images)

    if args.save_test_scores:
        with open(f'{args.language}_test_scores.json', 'w', encoding='utf-8') as outfile:
            json.dump(test_scores, outfile, ensure_ascii=False)


if __name__ == "__main__":
    main()
