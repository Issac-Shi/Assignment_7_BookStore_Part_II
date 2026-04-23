from flask import Flask, render_template, request, redirect, url_for
import os
import sqlite3

app = Flask(__name__)
DATABASE = "bookstore.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/", methods=["GET"])
def home():
    conn = get_db_connection()

    categories = conn.execute("""
        SELECT *
        FROM category
        ORDER BY categoryName
    """).fetchall()

    conn.close()

    return render_template("index.html", categories=categories)


@app.route("/category", methods=["GET"])
def category():
    category_id = request.args.get("categoryId", type=int)

    conn = get_db_connection()

    categories = conn.execute("""
        SELECT *
        FROM category
        ORDER BY categoryName
    """).fetchall()

    selected_category = conn.execute("""
        SELECT *
        FROM category
        WHERE categoryId = ?
    """, (category_id,)).fetchone()

    books = conn.execute("""
        SELECT *
        FROM book
        WHERE categoryId = ?
        ORDER BY title
    """, (category_id,)).fetchall()

    conn.close()

    return render_template(
        "category.html",
        categories=categories,
        selectedCategory=selected_category,
        books=books,
        searchTerm=None,
        nothingFound=False,
        pageTitle=None
    )


@app.route("/search", methods=["POST"])
def search():
    term = request.form.get("search", "").strip()

    conn = get_db_connection()

    categories = conn.execute("""
        SELECT *
        FROM category
        ORDER BY categoryName
    """).fetchall()

    books = conn.execute("""
        SELECT *
        FROM book
        WHERE lower(title) LIKE lower(?)
        ORDER BY title
    """, (f"%{term}%",)).fetchall()

    conn.close()

    return render_template(
        "category.html",
        categories=categories,
        selectedCategory=None,
        books=books,
        searchTerm=term,
        nothingFound=(len(books) == 0),
        pageTitle=None
    )

# new feature here: ReadNow
@app.route("/read-now", methods=["GET"])
def read_now():
    conn = get_db_connection()

    categories = conn.execute("""
        SELECT *
        FROM category
        ORDER BY categoryName
    """).fetchall()

    books = conn.execute("""
        SELECT *
        FROM book
        WHERE readNow = 1
        ORDER BY title
    """).fetchall()

    conn.close()

    return render_template(
        "category.html",
        categories=categories,
        selectedCategory=None,
        books=books,
        searchTerm=None,
        nothingFound=(len(books) == 0),
        pageTitle="Read Now Picks"
    )


@app.route("/book", methods=["GET"])
def book_detail():
    book_id = request.args.get("bookId", type=int)

    conn = get_db_connection()

    categories = conn.execute("""
        SELECT * FROM category ORDER BY categoryName
    """).fetchall()

    book = conn.execute("""
        SELECT book.*, category.categoryName
        FROM book
        JOIN category ON book.categoryId = category.categoryId
        WHERE book.bookId = ?
    """, (book_id,)).fetchone()

    conn.close()

    return render_template(
        "book_detail.html",
        book=book,
        categories=categories
    )


# @app.route("/add-book", methods=["GET", "POST"])
# def add_book():
#     conn = get_db_connection()

#     categories = conn.execute("""
#         SELECT * FROM category ORDER BY categoryName
#     """).fetchall()

#     if request.method == "POST":
#         title = request.form.get("title")
#         author = request.form.get("author")
#         isbn = request.form.get("isbn")
#         price = request.form.get("price", type=float)
#         image = request.form.get("image")
#         category_id = request.form.get("categoryId", type=int)

#         conn.execute("""
#             INSERT INTO book (categoryId, title, author, isbn, price, image, readNow)
#             VALUES (?, ?, ?, ?, ?, ?, 0)
#         """, (category_id, title, author, isbn, price, image))

#         conn.commit()
#         conn.close()

#         return redirect(url_for("home"))

#     conn.close()
#     return render_template("add_book.html", categories=categories)

# modify this code to check the validility of new added books
@app.route("/add-book", methods=["GET", "POST"])
def add_book():
    conn = get_db_connection()

    categories = conn.execute("""
        SELECT * FROM category ORDER BY categoryName
    """).fetchall()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        isbn = request.form.get("isbn", "").strip()
        price = request.form.get("price", type=float)
        image = request.form.get("image", "").strip()
        category_id = request.form.get("categoryId", type=int)

        if not title or not author or not isbn or not image or category_id is None or price is None:
            conn.close()
            return render_template("error.html", error="Please fill in all fields."), 400

        if price <= 0:
            conn.close()
            return render_template("error.html", error="Price must be greater than 0."), 400

        safe_image = os.path.basename(image)
        if safe_image != image:
            conn.close()
            return render_template("error.html", error="Invalid image filename."), 400

        image_path = os.path.join(app.static_folder, "images", "books", safe_image)
        if not os.path.exists(image_path):
            conn.close()
            return render_template(
                "error.html",
                error=f"Image file '{safe_image}' was not found in static/images/books/."
            ), 400

        existing_isbn = conn.execute("""
            SELECT bookId
            FROM book
            WHERE isbn = ?
        """, (isbn,)).fetchone()

        if existing_isbn:
            conn.close()
            return render_template("error.html", error="This ISBN already exists."), 400

        conn.execute("""
            INSERT INTO book (categoryId, title, author, isbn, price, image, readNow)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (category_id, title, author, isbn, price, safe_image))

        conn.commit()
        conn.close()

        return redirect(url_for("home"))

    conn.close()
    return render_template("add_book.html", categories=categories)

@app.errorhandler(Exception)
def handle_error(e):
    return render_template("error.html", error=e), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
