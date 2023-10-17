from flask import Flask, render_template, request
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import webbrowser
import threading
import subprocess
import random
import sys

app = Flask(__name__)

# Configuração da API do Spotify
CLIENT_ID = 'd1a8d6f13bf3478996d87fe63fc176e0'
CLIENT_SECRET = '15dea5369c024921814117ca93e83e7d'

sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET))

def get_random_track(query, artist):
    # Pega uma lista de faixas populares no momento
    search_query = f"{query} {artist}" if artist else query
    results = sp.search(q=search_query, type='track', limit=50)['tracks']['items']

    if not results:
        print(f"Não foi possível encontrar faixas para a consulta: {search_query}.")
        return None

    # Escolhe uma faixa aleatória
    random_track = random.choice(results)

    return {
        'id': random_track['id'],
        'name': random_track['name'],
        'artist': random_track['artists'][0]['name'],
        'artist_id': random_track['artists'][0]['id']
    }


def get_artist_genre(artist_id):
    # Obtém informações do artista para obter o gênero
    artist_info = sp.artist(artist_id)
    genres = artist_info['genres'] if 'genres' in artist_info else []
    return genres


def get_track_features(track_id):
    track_info = sp.track(track_id)
    features = sp.audio_features(track_id)

    if not track_info or not features or not features[0]:
        print(f"Não foi possível obter características para a música com ID {track_id}.")
        return None

    # Extrair características relevantes da música
    track_features = {
        'id': track_id,
        'name': track_info['name'],
        'artist': track_info['artists'][0]['name'],
        'danceability': features[0]['danceability'],
        'energy': features[0]['energy'],
        'loudness': features[0]['loudness'],
        'speechiness': features[0]['speechiness'],
        'acousticness': features[0]['acousticness'],
        'instrumentalness': features[0]['instrumentalness'],
        'valence': features[0]['valence'],
        'mode': features[0]['mode'],
        'tempo': features[0]['tempo'],
        'genre': get_artist_genre(track_info['artists'][0]['id'])
    }
    return track_features


def recommend_tracks(user_input_name, user_input_artist):
    # Pega uma música aleatória do artista, se fornecido
    seed_track_info = get_random_track(user_input_name, user_input_artist)

    if not seed_track_info:
        print(f"Não foi possível obter uma música aleatória para a consulta: {user_input_name} {user_input_artist}.")
        return

    # Obtém as características da música semente
    seed_track_features = get_track_features(seed_track_info['id'])

    if not seed_track_features:
        print(
            f"Não foi possível obter características para a música semente ({seed_track_info['name']} by {seed_track_info['artist']}).")
        return

    # Obtém as características de músicas recomendadas com base na música semente
    recommendations_same_artist = \
    sp.recommendations(seed_tracks=[seed_track_info['id']], limit=5, seed_artists=[seed_track_info['artist_id']])[
        'tracks']

    recommendation_features_same_artist = [get_track_features(track['id']) for track in recommendations_same_artist]

    # Se houver recomendações suficientes do mesmo artista, use-as
    if len(recommendation_features_same_artist) >= 5:
        final_recommendations = recommendation_features_same_artist
    else:
        # Caso contrário, obtenha recomendações adicionais
        remaining_recommendations = \
        sp.recommendations(seed_tracks=[seed_track_info['id']], limit=5 - len(recommendation_features_same_artist))[
            'tracks']
        recommendation_features_remaining = [get_track_features(track['id']) for track in remaining_recommendations]

        # Combine as recomendações do mesmo artista com as adicionais
        final_recommendations = recommendation_features_same_artist + recommendation_features_remaining

    return final_recommendations


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_input_name = request.form['track_name']
        user_input_artist = request.form['artist_name']

        recommended_tracks = recommend_tracks(user_input_name, user_input_artist)

        return render_template('template.html', recommended_tracks=recommended_tracks)

    return render_template('template.html', recommended_tracks=[])

def open_browser():
    # Abre o navegador após a execução do servidor Flask
    webbrowser.open('http://127.0.0.1:5000/')

if __name__ == '__main__':
    
    # Obtém o caminho absoluto do script atual
    import os
    current_script_path = os.path.abspath(__file__)
    
   # Desativa o reloader para evitar o erro de thread
    app.run(debug=True, use_reloader=False)
    
    # Aguarda um momento para garantir que o servidor Flask esteja pronto
    import time
    time.sleep(2)

    # Abre o navegador automaticamente
    open_browser()