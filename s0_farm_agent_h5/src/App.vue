<script setup>
import { computed, nextTick, ref } from 'vue'
import {
  Bot,
  MessageCirclePlus,
  Mic,
  Send,
  Sparkles,
  UserRound,
} from 'lucide-vue-next'

const inputMode = ref('voice')
const textValue = ref('')
const isRecording = ref(false)
const messagesEl = ref(null)
const conversationVersion = ref(0)

const messages = ref([
  {
    id: 1,
    role: 'user',
    text: '给A区番茄安排明天上午浇水，负责人李四'
  },
  {
    id: 2,
    role: 'agent',
    text:
      '已识别为“创建农事任务”。\n\n待执行操作步骤：\n1. 查询 A 区当前番茄种植批次。\n2. 检查李四明天上午的任务排程。\n3. 待创建浇水任务，时间为明天上午，负责人李四。\n\n需要确认：具体时间段、浇水量或时长。'
  }
])

const inputPlaceholder = computed(() =>
  inputMode.value === 'text' ? '输入农场管理需求' : '按住说话'
)

function scrollToBottom() {
  nextTick(() => {
    if (messagesEl.value) {
      messagesEl.value.scrollTop = messagesEl.value.scrollHeight
    }
  })
}

function toggleInputMode() {
  inputMode.value = inputMode.value === 'voice' ? 'text' : 'voice'
  isRecording.value = false
}

function startNewConversation() {
  conversationVersion.value += 1
  messages.value = []
  textValue.value = ''
  isRecording.value = false
  scrollToBottom()
}

function sendText() {
  const text = textValue.value.trim()
  if (!text) return

  messages.value.push({
    id: Date.now(),
    role: 'user',
    text
  })
  textValue.value = ''
  scrollToBottom()
  replyWithPlan(text)
}

function replyWithPlan(text) {
  const currentVersion = conversationVersion.value
  const thinkingId = Date.now() + 1
  messages.value.push({
    id: thinkingId,
    role: 'agent',
    thinking: true,
    text: '思考中'
  })
  scrollToBottom()

  window.setTimeout(() => {
    if (currentVersion !== conversationVersion.value) return

    const index = messages.value.findIndex((item) => item.id === thinkingId)
    if (index >= 0) {
      messages.value[index] = {
        id: thinkingId,
        role: 'agent',
        text:
          `已解析需求：${text}\n\n` +
          '待执行操作步骤：\n' +
          '1. 查询相关地块、作物批次和负责人信息。\n' +
          '2. 校验时间、人员排程和任务冲突。\n' +
          '3. 生成待创建农事任务预览。\n\n' +
          '需要确认：具体时间、用量/时长、是否立即提交。'
      }
    }
    scrollToBottom()
  }, 900)
}

function startVoice() {
  if (inputMode.value !== 'voice') return
  isRecording.value = true
}

function endVoice() {
  if (!isRecording.value) return
  isRecording.value = false

  const voiceText = '语音输入：给B区草莓生成今天的巡检任务'
  messages.value.push({
    id: Date.now(),
    role: 'user',
    text: voiceText
  })
  scrollToBottom()
  replyWithPlan('给B区草莓生成今天的巡检任务')
}
</script>

<template>
  <main class="phone-shell">
    <section class="app-screen">
      <div class="quick-actions" aria-label="快捷操作">
        <button class="round-button" aria-label="新会话" @click="startNewConversation">
          <MessageCirclePlus :size="25" />
        </button>
      </div>

      <div ref="messagesEl" class="chat-list">
        <section v-if="messages.length === 0" class="empty-state">
          <div class="empty-icon">
            <Bot :size="28" />
          </div>
          <h1>农场智管</h1>
          <p>今天想处理哪块地？</p>
        </section>

        <article
          v-for="message in messages"
          :key="message.id"
          :class="['message-row', message.role]"
        >
          <div v-if="message.role === 'agent'" class="avatar">
            <Bot :size="19" />
          </div>
          <div :class="['bubble', { thinking: message.thinking }]">
            <span>{{ message.text }}</span>
            <span v-if="message.thinking" class="typing-dots">
              <i></i><i></i><i></i>
            </span>
          </div>
          <div v-if="message.role === 'user'" class="avatar user-avatar">
            <UserRound :size="18" />
          </div>
        </article>
      </div>

      <footer class="composer-wrap">
        <div class="composer">
          <button
            class="mode-button"
            :aria-label="inputMode === 'voice' ? '切换到文本输入' : '切换到语音输入'"
            @click="toggleInputMode"
          >
            <Sparkles v-if="inputMode === 'voice'" :size="25" />
            <Mic v-else :size="24" />
          </button>

          <button
            v-if="inputMode === 'voice'"
            :class="['voice-button', { recording: isRecording }]"
            @mousedown="startVoice"
            @mouseup="endVoice"
            @mouseleave="endVoice"
            @touchstart.prevent="startVoice"
            @touchend.prevent="endVoice"
          >
            {{ isRecording ? '松开发送' : inputPlaceholder }}
          </button>

          <form v-else class="text-form" @submit.prevent="sendText">
            <input
              v-model="textValue"
              :placeholder="inputPlaceholder"
              autocomplete="off"
            />
            <button class="send-button" type="submit" aria-label="发送">
              <Send :size="20" />
            </button>
          </form>
        </div>
        <div class="home-indicator"></div>
      </footer>
    </section>
  </main>
</template>
