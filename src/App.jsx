import './App.css'

const categories = [
  { id: 'crypto', number: '01', label: 'Cryptography only' },
  { id: 'steganography', number: '02', label: 'Steganography only' },
  { id: 'combined', number: '03', label: 'Cryptography + steganography' },
  { id: 'detection', number: '04', label: 'Stego Detection' },
]

function App() {
  return (
    <main className="home" aria-label="Cryptography and steganography">
      <h1 className="visually-hidden">Choose a category</h1>
      <section className="category-grid" aria-label="Categories">
        {categories.map(({ id, number, label }, index) => {
          const cardContent = (
            <>
              <span className="category-number" aria-hidden="true">
                {number}
              </span>
              <h2>{label}</h2>
              <span className="category-mark" aria-hidden="true" />
            </>
          )
          const cardClassName = `category-card category-card--${id}`
          const cardStyle = { '--card-index': index }

          return (
            <a
              className={cardClassName}
              href={`/${id}`}
              key={id}
              style={cardStyle}
            >
              {cardContent}
            </a>
          )
        })}
      </section>
    </main>
  )
}

export default App
