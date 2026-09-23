import {
  useEffect,
  useRef,
  useState,
} from "react"


const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL


const EXAMPLES = [
  "12와 34를 곱해줘.",
  "13과 29를 더해줘.",
  "LangGraph 수업에서는 무엇을 배우는지 알려줘.",
]


function App() {
  const [
    input,
    setInput,
  ] = useState("")


  const [
    messages,
    setMessages,
  ] = useState([
    {
      id: crypto.randomUUID(),

      role:
        "assistant",

      content:
        (
          "안녕하세요. "
          + "FastAPI 뒤에 연결된 "
          + "LangGraph Agent입니다."
        ),
    },
  ])


  const [
    loading,
    setLoading,
  ] = useState(false)


  const [
    error,
    setError,
  ] = useState("")


  const messagesEndRef =
    useRef(null)


  useEffect(
    () => {
      messagesEndRef.current
        ?.scrollIntoView({
          behavior:
            "smooth",
        })
    },

    [
      messages,
      loading,
    ]
  )


  const sendMessage =
    async (
      directMessage = null
    ) => {

      const message = (
        directMessage
        ??
        input
      ).trim()


      if (!message) {
        return
      }


      const userMessage = {
        id:
          crypto.randomUUID(),

        role:
          "user",

        content:
          message,
      }


      const assistantId =
        crypto.randomUUID()


      const assistantMessage = {
        id:
          assistantId,

        role:
          "assistant",

        content:
          "",
      }


      setMessages(
        (previousMessages) => [
          ...previousMessages,
          userMessage,
          assistantMessage,
        ]
      )


      setInput("")
      setError("")
      setLoading(true)


      try {
        const response =
          await fetch(
            `${API_BASE_URL}/api/agent/stream`,

            {
              method:
                "POST",

              headers: {
                "Content-Type":
                  "application/json",
              },

              body:
                JSON.stringify({
                  message:
                    message,
                }),
            }
          )


        if (!response.ok) {
          const errorData =
            await response.json()

          const detail = (
            typeof errorData.detail
            ===
            "string"
          )
          ?
          errorData.detail
          :
          JSON.stringify(
            errorData.detail
          )


          throw new Error(
            detail
            ||
            `HTTP ${response.status}`
          )
        }


        if (!response.body) {
          throw new Error(
            (
              "Streaming Response "
              + "Body가 없습니다."
            )
          )
        }


        const reader =
          response.body.getReader()


        const decoder =
          new TextDecoder(
            "utf-8"
          )


        while (true) {
          const {
            done,
            value,
          } = await reader.read()


          if (done) {
            break
          }


          const chunk =
            decoder.decode(
              value,

              {
                stream:
                  true,
              }
            )


          setMessages(
            (previousMessages) =>
              previousMessages.map(
                (currentMessage) => {

                  if (
                    currentMessage.id
                    ===
                    assistantId
                  ) {
                    return {
                      ...currentMessage,

                      content:
                        (
                          currentMessage.content
                          +
                          chunk
                        ),
                    }
                  }


                  return (
                    currentMessage
                  )
                }
              )
          )
        }


      } catch (err) {
        setError(
          (
            "LangGraph Agent 요청 실패: "
            + err.message
          )
        )


        setMessages(
          (previousMessages) =>
            previousMessages.filter(
              (currentMessage) =>
                currentMessage.id
                !==
                assistantId
            )
        )


      } finally {
        setLoading(false)
      }
    }


  const handleKeyDown =
    (event) => {

      if (
        event.key === "Enter"
        &&
        !event.shiftKey
      ) {
        event.preventDefault()

        sendMessage()
      }
    }


  const clearMessages = () => {
    setMessages([
      {
        id:
          crypto.randomUUID(),

        role:
          "assistant",

        content:
          (
            "대화를 초기화했습니다. "
            + "새로운 질문을 입력하세요."
          ),
      },
    ])

    setError("")
  }


  return (
    <main className="page">

      <section className="chat">

        <header className="chat-header">

          <div>
            <h1>
              LangGraph Agent
            </h1>

            <p>
              React + FastAPI + LangGraph + Gemini
            </p>
          </div>


          <button
            className="clear-button"

            onClick={
              clearMessages
            }

            disabled={
              loading
            }
          >
            대화 초기화
          </button>

        </header>


        <div className="examples">

          {
            EXAMPLES.map(
              (example) => (

                <button
                  key={
                    example
                  }

                  onClick={
                    () =>
                      sendMessage(
                        example
                      )
                  }

                  disabled={
                    loading
                  }
                >
                  {example}
                </button>
              )
            )
          }

        </div>


        <div className="messages">

          {
            messages.map(
              (message) => (

                <div
                  key={
                    message.id
                  }

                  className={
                    (
                      "message-row "
                      + message.role
                    )
                  }
                >

                  <div
                    className="message-label"
                  >
                    {
                      message.role
                      ===
                      "user"
                      ?
                      "You"
                      :
                      "Agent"
                    }
                  </div>


                  <div
                    className="message-bubble"
                  >
                    {
                      message.content
                      ||
                      (
                        loading
                        ?
                        "Agent 실행 중..."
                        :
                        ""
                      )
                    }
                  </div>

                </div>
              )
            )
          }


          <div
            ref={
              messagesEndRef
            }
          />

        </div>


        {
          error
          &&
          (
            <div className="error">
              {error}
            </div>
          )
        }


        <div className="input-area">

          <textarea
            value={
              input
            }

            onChange={
              (event) =>
                setInput(
                  event.target.value
                )
            }

            onKeyDown={
              handleKeyDown
            }

            placeholder={
              "Agent에게 질문하세요. "
              + "Enter: 전송 / "
              + "Shift+Enter: 줄바꿈"
            }

            disabled={
              loading
            }
          />


          <button
            className="send-button"

            onClick={
              () =>
                sendMessage()
            }

            disabled={
              loading
              ||
              !input.trim()
            }
          >
            {
              loading
              ?
              "실행 중"
              :
              "전송"
            }
          </button>

        </div>


        <footer className="footer">
          <span>
            Agent API:
          </span>

          <strong>
            {
              `${API_BASE_URL}/api/agent/stream`
            }
          </strong>
        </footer>

      </section>

    </main>
  )
}


export default App
