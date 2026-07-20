-- Удаляем MS Office теги на этапе RawBlock
function RawBlock(el)
    if el.format == "htm" then
        -- Удаляем smart tags и другие MS Office теги
        el.text = el.text:gsub("</?o:[^>]+>", "")
        el.text = el.text:gsub("</?st1:[^>]+>", "")
        el.text = el.text:gsub("</?w:[^>]+>", "")
        el.text = el.text:gsub("</?m:[^>]+>", "")
        el.text = el.text:gsub("</?v:[^>]+>", "")
        return el
    end
end

-- Остальные ваши функции...
-- Сохраняем информацию об изображениях как текст для RAG
function Image(el)
  local caption_text = pandoc.utils.stringify(el.caption or {})
  local img_md = "![" .. caption_text .. "](" .. el.src .. ")"
  return pandoc.RawInline('markdown', img_md)
end

-- Удаляем спаны
function Span(el)
  return el.content
end

-- Чистим заголовки, сохраняя структуру
function Header(el)
  el = pandoc.walk_block(el, {
    Span = function(s) return s.content end
  })
  el.identifier = ""
  el.attributes = {}
  return el
end

-- Внешние ссылки оставляем как текст с URL
function Link(el)
  if el.target:match("^https?://") then
    return el
  end
  -- Для внутренних ссылок сохраняем текст ссылки
  local link_text = pandoc.utils.stringify(el.content)
  if link_text and link_text ~= "" then
    return pandoc.Str(link_text)
  end
  return el.content
end

-- Раскрываем div
function Div(el)
  return el.content
end

-- Таблицы без изменений
function Table(el)
  return el
end