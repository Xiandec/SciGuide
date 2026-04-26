#let page-number() = context {
  let current = counter(page).get().first()
  if current > 1 [
    #set text(size: 12pt)
    #align(center)[#counter(page).display("1")]
  ]
}

#let title-page() = [
  #set align(center)
  #set text(size: 12pt)
  #set par(
    justify: false,
    first-line-indent: 0cm,
    leading: 1.12em,
    spacing: 0em,
  )

  #text(size: 10.5pt)[
    $if(ministry-line-1)$$ministry-line-1$$endif$ \
    $if(ministry-line-2)$$ministry-line-2$$endif$
  ]

  #v(0.22cm)

  #text(size: 11pt, weight: "bold")[
    $if(university-name-line-1)$«$university-name-line-1$$endif$ \
    $if(university-name-line-2)$$university-name-line-2$»$endif$ \
    $if(university-short-name)$($university-short-name$)$endif$
  ]

  #v(0.55cm)

  #text(size: 11pt)[
    $if(department)$$department$$endif$ \
    $if(institute)$$institute$$endif$
  ]

  #v(0.95cm)

  #text(size: 11pt, style: "italic")[
    $if(discipline)$Дисциплина: «$discipline$»$endif$ \
    $if(study-direction)$Направление подготовки: «$study-direction$»$endif$ \
    $if(profile)$Профиль: «$profile$»$endif$ \
    $if(institute)$$institute$$endif$ \
    $if(study-form)$Форма обучения $study-form$$endif$ \
    $if(academic-year)$Учебный $academic-year$ год$endif$$if(semester)$, $semester$ семестр$endif$
  ]

  #v(3.05cm)

  #text(weight: "bold")[
    $if(work-kind)$$work-kind$ на тему:$endif$
  ]

  #v(0.15cm)

  #text(weight: "bold")[
    «$title$»
  ]

  #v(3.0cm)

  #align(right)[
    #block(width: 7.2cm)[
      #set align(right)
      #text(style: "italic")[Выполнил(а):] \
      #v(0.5cm)
      студент(ка) группы $if(group)$$group$$endif$ \
      #v(0.5cm)
      $if(student)$$student$$endif$ \
      #v(1.15cm)
      #text(style: "italic")[Научный руководитель:] \
      #v(0.5cm)
      $if(supervisor)$$supervisor$$endif$
    ]
  ]

  #v(1fr)

  #align(center)[
    $if(city)$$city$$endif$ $if(year)$$year$$endif$
  ]
]

#set page(
  paper: "$papersize$",
  margin: ($for(margin/pairs)$$margin.key$: $margin.value$,$endfor$),
  header: none,
  footer: page-number(),
  header-ascent: 2cm,
  footer-descent: 1.25cm,
)

#set text(
  font: ("$mainfont$",),
  size: $fontsize$,
  lang: "$lang$",
)

#set par(
  justify: true,
  first-line-indent: 1.25cm,
  leading: $linestretch$ * 0.65em,
  spacing: 0.5cm,
)

#show emph: it => it.body
#show ref.where(form: "normal"): set ref(supplement: el => {
  if el.func() == figure {
    if el.kind == table {
      [табл.]
    } else if el.kind == raw {
      [листинг]
    } else {
      [рис.]
    }
  } else {
    auto
  }
})

#show raw: set text(font: ("$codefont$",), size: 11pt)
#show raw.where(block: true): set block(
  inset: 10pt,
  stroke: (paint: luma(180), thickness: 0.6pt),
  radius: 3pt,
)

#show figure.where(kind: image): set figure(supplement: [Рисунок])
#show figure.where(kind: table): set figure(supplement: [Таблица])
#show figure.where(kind: raw): set figure(supplement: [Листинг])
#show figure.where(kind: table): set figure.caption(position: top)
#show figure.where(kind: image): set figure.caption(position: bottom)
#show figure.where(kind: raw): set figure.caption(position: bottom)
#show figure.caption: set text(size: 12pt)
#show figure.caption: set par(
  first-line-indent: 0cm,
  leading: 0.65em,
  spacing: 0em,
)

#show table: set table(
  inset: 4pt,
  stroke: (paint: black, thickness: 0.5pt),
)
#show table.cell: set text(size: 12pt)
#show table.cell: set par(
  first-line-indent: 0cm,
  leading: 0.65em,
  spacing: 0em,
)

#show footnote.entry: set text(size: 10pt)
#show footnote.entry: set par(
  first-line-indent: 0cm,
  leading: 0.65em,
  spacing: 0em,
)

#show heading.where(level: 1): it => [
  #pagebreak()
  #it
]
#show heading.where(level: 1): set block(above: 2cm, below: 1cm)
#show heading.where(level: 1): set text(size: 16pt, weight: "bold")
#show heading.where(level: 1): set align(center)
#show heading.where(level: 1): set par(
  first-line-indent: 0cm,
  leading: 0.65em,
  spacing: 0em,
)

#show heading.where(level: 2): set block(above: 1cm, below: 0.5cm)
#show heading.where(level: 2): set text(size: 14pt, weight: "bold")
#show heading.where(level: 2): set par(
  first-line-indent: 0cm,
  leading: 0.65em,
  spacing: 0em,
)

#show heading.where(level: 3): set block(above: 0.7cm, below: 0.3cm)
#show heading.where(level: 3): set text(size: 14pt, weight: "bold")
#show heading.where(level: 3): set par(
  first-line-indent: 0cm,
  leading: 0.65em,
  spacing: 0em,
)

#title-page()

#outline(title: [Оглавление])

$body$
