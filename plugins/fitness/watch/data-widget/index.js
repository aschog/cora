import { createWidget, widget, align, prop, sport_data, edit_widget_group_type } from '@zos/ui'
import { BasePage } from '@zeppos/zml/base-page'
import { NOTICE } from '../config'    // written by `make watch`: where this watch's cora is

// One screen inside a system workout. The lifter starts and ends the workout as always
// and Zepp keeps its own record; this writes the fitness field's notice, so the trainer
// page starts its workout when the wrist does and saves it when the control is tapped.
//
// The tap is the design, not a shortcut. Nothing sent as a workout extension is torn
// down reaches the phone: a probe posting from every lifecycle point over five workouts
// was heard at onInit and onPause and never once at onDestroy, and onPause cannot stand
// in because it fires identically on every swipe away from this screen. So the end of
// the workout is a thing the lifter says, and a workout extension supports click events
// on its widgets where it refuses gestures and the side button.
const W = 480
const RUNNING = 'running'
const FINISHED = 'finished'

const DURATION = {
  edit_id: 1, x: 40, y: 110, w: W - 80, h: 140, category: edit_widget_group_type.SPORTS,
  default_type: sport_data.DURATION_NET, optional_types: [sport_data.DURATION_NET],
  count: 1, rect_visible: false,
  text_size: 96, text_color: 0xffffff, text_x: 0, text_y: 0, text_w: W - 80, text_h: 106,
  sub_text_visible: true, sub_text_size: 24, sub_text_color: 0x868d99,
  sub_text_x: 0, sub_text_y: 106, sub_text_w: W - 80, sub_text_h: 30,
}

DataWidget(BasePage({
  state: { done: false },

  // A workout begins. `state` is one object for the life of the app rather than one per
  // page, so last workout's tap is still in it and this is where it is put back.
  onInit() {
    this.state.done = false
    this.write(RUNNING)
  },

  build() {
    createWidget(widget.SPORT_DATA, DURATION)
    createWidget(widget.BUTTON, {
      x: 90, y: 280, w: W - 180, h: 72, radius: 36,
      normal_color: 0x1a4d8f, press_color: 0x2f7bd6,
      text: 'Finish & save', text_size: 28, color: 0xffffff,
      click_func: () => this.finish(),
    })
    this.link = createWidget(widget.TEXT, {
      x: 0, y: 380, w: W, h: 40, text_size: 24, color: 0x868d99,
      align_h: align.CENTER_H, text: '',
    })
  },

  // Once per workout. A second tap would save a workout the page has already started
  // fresh, and onInit is what makes the next workout's tap the first one again.
  finish() {
    if (this.state.done) return
    this.state.done = true
    this.say('saving')
    // Spent only once cora has it. A phone that could not reach the machine — asleep,
    // off the network — leaves the lifter standing there with the workout still theirs
    // to save, so the control comes back rather than staying dead.
    this.write(FINISHED).then((took) => { if (!took) this.state.done = false })
  },

  // What the wrist is told is the line under the clock and never the button's own
  // label: one widget says everything, so there is one property to be right about.
  write(workout) {
    const word = workout === FINISHED ? 'saved' : 'linked'
    return this.httpRequest({
      method: 'PUT', url: NOTICE, headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ workout }),
    })
      .then((r) => {
        this.say(r.status === 200 ? word : 'refused ' + r.status + ' - tap again')
        return r.status === 200
      })
      .catch((e) => {
        this.say('no link - tap again: ' + String((e && e.message) || e).slice(0, 28))
        return false
      })
  },

  // The build may not have run yet when the first write comes back, onInit being before
  // it — so the screen is told what it missed the moment it exists.
  say(line) {
    this.state.line = line
    if (this.link) this.link.setProperty(prop.TEXT, line)
  },

  onResume() {
    if (this.state.line) this.say(this.state.line)
  },
}))
