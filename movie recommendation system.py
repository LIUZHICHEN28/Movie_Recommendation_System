import streamlit as st
import pandas as pd
from collections import Counter

st.set_page_config(layout="wide")


class Movie:
    def __init__(self, movie_id, title, genre, year):
        self.movie_id = movie_id
        self.title = title
        self.genre = genre
        self.year = year
        self.ratings = []
        self.views = 0

    def add_rating(self, rating):
        self.ratings.append(rating)

    def add_view(self):
        self.views += 1

    def get_average_rating(self):
        return sum(self.ratings)/len(self.ratings) if self.ratings else 0


class User:
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name
        self.view_history = []
        self.given_ratings = {}

    def watch_movie(self, movie):
        self.view_history.append(movie)
        movie.add_view()

    def rate_movie(self, movie, rating):
        self.given_ratings[movie.movie_id] = rating
        movie.add_rating(rating)


class RecommendationSystem:
    def __init__(self):
        self.movies = {}
        self.users = {}

    def add_movie(self, movie):
        self.movies[movie.movie_id] = movie

    def add_user(self, user):
        self.users[user.user_id] = user

    def generate_recommendations(self, user_id, top_n=3):
        user = self.users.get(user_id)
        if not user:
            return []

        #User preferences (types viewed)
        genre_count = Counter([m.genre for m in user.view_history])

        if genre_count:
            favorite_genres = [g for g, c in genre_count.items() if c == max(genre_count.values())]
        else:
            #If haven't seen it, use popular genre
            favorite_genres = [self.get_most_popular_genre()]

        watched_ids = {m.movie_id for m in user.view_history}

        scored_movies = []

        for m in self.movies.values():
            if m.movie_id in watched_ids:
                continue


            avg_rating = m.get_average_rating()
            views = m.views


            genre_bonus = 1 if m.genre in favorite_genres else 0


            score = avg_rating * 0.6 + views * 0.3 + genre_bonus * 2

            scored_movies.append((score, m))

        scored_movies.sort(key=lambda x: x[0], reverse=True)

        return [m for _, m in scored_movies[:top_n]]

    def get_most_popular_genre(self):
        genre_views = {}
        for m in self.movies.values():
            genre_views[m.genre] = genre_views.get(m.genre, 0) + m.views
        return max(genre_views, key=genre_views.get) if genre_views else None

    def get_trending_movies(self):
        return sorted(self.movies.values(), key=lambda x: x.views, reverse=True)[:3]


if "system" not in st.session_state:
    system = RecommendationSystem()


    movies = [
        ("1", "Inception", "Sci-Fi", 2010, [5, 5, 4, 5], 120),
        ("2", "Interstellar", "Sci-Fi", 2014, [5, 4, 5, 5], 150),
        ("3", "The Dark Knight", "Action", 2008, [5, 5, 5, 4], 200),
        ("4", "Avengers", "Action", 2012, [4, 4, 5, 4], 180),
        ("5", "Titanic", "Romance", 1997, [5, 5, 4], 220),
        ("6", "La La Land", "Romance", 2016, [4, 5, 4], 90),
        ("7", "Matrix", "Sci-Fi", 1999, [5, 5, 5], 160),
        ("8", "John Wick", "Action", 2014, [4, 4, 5], 140),
    ]

    for mid, title, genre, year, ratings, views in movies:
        movie = Movie(mid, title, genre, year)

        #add initial rating
        for r in ratings:
            movie.add_rating(r)

        #set initial heat
        movie.views = views
        system.add_movie(movie)

    #users
    users = [
        ("u1","Alice"),
        ("u2","Bob"),
        ("u3","Charlie"),
        ("u4","Danny"),
        ("u5","Ella"),
        ("u6", "Fiona")
    ]

    for u in users:
        system.add_user(User(*u))

    st.session_state.system = system

system = st.session_state.system

#Sidebar Navigation
st.sidebar.title("Navigation")

view = st.sidebar.radio("Select View", ["User Dashboard", "Admin Console"])


#USER DASHBOARD
if view == "User Dashboard":

    st.title("🎬 User Dashboard")

    user_map = {u.name: u.user_id for u in system.users.values()}
    selected_name = st.selectbox("Login as:", list(user_map.keys()))
    user_id = user_map[selected_name]
    user = system.users[user_id]

    st.success(f"Welcome {user.name}")

    #search
    st.header("🔍 Advanced Search")

    title = st.text_input("Title Keyword")
    genre = st.selectbox("Genre", ["All"] + list(set(m.genre for m in system.movies.values())))
    year = st.selectbox("Year", ["All"] + sorted(set(m.year for m in system.movies.values())))

    if st.button("Search Movies"):
        conditions = sum([bool(title), genre!="All", year!="All"])

        if conditions < 2:
            st.warning("⚠ Please select at least TWO conditions!")
        else:
            results = []
            for m in system.movies.values():
                if title and title.lower() not in m.title.lower():
                    continue
                if genre!="All" and m.genre!=genre:
                    continue
                if year!="All" and m.year!=year:
                    continue
                results.append(m)

            if results:
                df = pd.DataFrame([{
                    "Title":m.title,
                    "Genre":m.genre,
                    "Year":m.year,
                    "Rating":round(m.get_average_rating(),2)
                } for m in results])
                st.dataframe(df)
            else:
                st.info("No results")

    #Watch and Rate
    st.header("🎥 Watch & Rate")

    movie_map = {m.title: m for m in system.movies.values()}
    selected_movie = st.selectbox("Select Movie", list(movie_map.keys()))

    rating = st.slider("Rating", 1, 5)

    if st.button("🎬 Watch & Submit Rating"):
        movie = movie_map[selected_movie]

        user.watch_movie(movie)
        user.rate_movie(movie, rating)

        st.success(f"You watched and rated {movie.title} ({rating}⭐)")

    #recommendations
    st.header("🎯 Recommendations")

    top_n = st.slider("Top N",1,5,3)
    recs = system.generate_recommendations(user_id,top_n)

    if recs:
        for m in recs:
            st.write(f"{m.title} ⭐ {m.get_average_rating():.2f}")
    else:
        st.info("No recommendations")

    #history
    st.header("📊 History")

    data = [{
        "Title":m.title,
        "Genre":m.genre,
        "Rating":user.given_ratings.get(m.movie_id,"N/A")
    } for m in user.view_history]

    if data:
        st.table(pd.DataFrame(data))

    #Insights
    st.header("📈 Insights")

    st.write("Most Popular Genre:", system.get_most_popular_genre())

    for m in system.get_trending_movies():
        st.write(f"{m.title} | Views:{m.views}")

    chart = pd.DataFrame([{
        "Movie":m.title,
        "Rating":m.get_average_rating()
    } for m in system.movies.values()])

    st.bar_chart(chart.set_index("Movie"))

# Admin
else:
    st.title("🔐 Admin Console")

    key = st.sidebar.text_input("Enter Admin Key", type="password")

    if key != "taylor123":
        st.info("Password is error! Enter admin key")
    else:
        st.success("Access successfully")

        tab1, tab2 = st.tabs(["Movie Management","Analytics"])

        #charge add or delete movie
        with tab1:
            st.subheader("Add Movie")

            mid = st.text_input("ID")
            title = st.text_input("Title")
            genre = st.text_input("Genre")
            year = st.number_input("Year",1900,2025)

            if st.button("Add Movie"):
                if not mid or not title or not genre or not year:
                    st.error("❌ All fields are required!")
                elif mid in system.movies:
                    st.error("Movie ID already exists!")
                else:
                    system.add_movie(Movie(mid, title, genre, year))
                    st.success("Movie added successfully!")

            st.subheader("Delete Movie")

            movie_names = {m.title: m.movie_id for m in system.movies.values()}

            if movie_names:
                selected_title = st.selectbox("Select Movie to Delete", list(movie_names.keys()))

                if st.button("Delete Movie"):
                    movie_id = movie_names[selected_title]
                    del system.movies[movie_id]
                    st.warning(f"{selected_title} deleted!")
            else:
                st.info("No movies available.")

        #analazy
        with tab2:
            st.subheader("Most Viewed Movies")
            for m in sorted(system.movies.values(), key=lambda x:x.views, reverse=True)[:5]:
                st.write(f"{m.title} | Views:{m.views}")

            st.subheader("Most Active Users")
            for u in sorted(system.users.values(), key=lambda x:len(x.view_history), reverse=True):
                st.write(f"{u.name} | Watches:{len(u.view_history)}")

            st.subheader("Popular Movies Score")

            def score(m):
                return m.get_average_rating()*0.7 + m.views*0.3

            for m in sorted(system.movies.values(), key=score, reverse=True)[:5]:
                st.write(f"{m.title} | Score:{score(m):.2f}")