import { BaseSideService } from '@zeppos/zml/base-side'

// Runs in the Zepp app on the phone. Nothing to do here: zml proxies the page's
// httpRequest through it, and the phone is what has the network.
AppSideService(BaseSideService({}))
